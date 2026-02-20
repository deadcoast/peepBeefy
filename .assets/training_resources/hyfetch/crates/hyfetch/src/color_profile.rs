use std::iter;
use std::num::{NonZeroU8, NonZeroUsize};

use anyhow::{anyhow, Result, Context as _};
use indexmap::IndexSet;
use palette::num::ClampAssign as _;
use palette::{IntoColorMut as _, LinSrgb, Okhsl, Srgb};
use tracing::debug;
use unicode_segmentation::UnicodeSegmentation as _;

use crate::color_util::{ForegroundBackground, Lightness, ToAnsiString as _};
use crate::types::{AnsiMode, TerminalTheme};

#[derive(Clone, Eq, PartialEq, Debug)]
pub struct ColorProfile {
    pub colors: Vec<Srgb<u8>>,
}

#[derive(Clone, PartialEq, Debug)]
pub enum AssignLightness {
    Replace(Lightness),
    ClampMax(Lightness),
    ClampMin(Lightness),
}

impl ColorProfile {
    pub fn new(colors: Vec<Srgb<u8>>) -> Self {
        Self { colors }
    }

    pub fn from_hex_colors<S>(hex_colors: Vec<S>) -> Result<Self>
    where
        S: AsRef<str>,
    {
        let colors = hex_colors
            .into_iter()
            .map(|s| s.as_ref().parse())
            .collect::<Result<_, _>>()
            .context("failed to parse hex colors")?;
        Ok(Self::new(colors))
    }

    /// Maps colors based on weights.
    ///
    /// # Arguments
    ///
    /// * `weights` - Weights of each color (`weights[i]` = how many times
    ///   `colors[i]` appears)
    pub fn with_weights(&self, weights: Vec<u8>) -> Result<Self> {
        if weights.len() != self.colors.len() {
            debug!(?weights, ?self.colors, "length mismatch between `weights` and `colors`");
            return Err(anyhow!(
                "`weights` should have the same number of elements as `colors`"
            ));
        }

        let mut weighted_colors = Vec::new();

        for (i, w) in weights.into_iter().enumerate() {
            weighted_colors.extend(iter::repeat(self.colors[i]).take(usize::from(w)));
        }

        Ok(Self::new(weighted_colors))
    }

    /// Creates a new color profile, with the colors spread to the specified
    /// length.
    pub fn with_length(&self, length: NonZeroU8) -> Result<Self> {
        let orig_len = self.colors.len();
        let orig_len: NonZeroUsize = orig_len.try_into().expect("`colors` should not be empty");
        let orig_len: NonZeroU8 = orig_len
            .try_into()
            .expect("`colors` should not have more than 255 elements");
        // TODO: I believe weird things can happen because of this...
        // if length < orig_len {
        //     unimplemented!("compressing length of color profile not implemented");
        // }
        let center_i = usize::from(orig_len.get() / 2);

        // How many copies of each color should be displayed at least?
        let repeats = length.get().div_euclid(orig_len.get());
        let mut weights = vec![repeats; NonZeroUsize::from(orig_len).get()];

        // How many extra spaces left?
        let mut extras = length.get().rem_euclid(orig_len.get());

        // If there is an odd space left, extend the center by one space
        if extras % 2 == 1 {
            weights[center_i] = weights[center_i].checked_add(1).unwrap();
            extras = extras.checked_sub(1).unwrap();
        }

        // Add weight to border until there's no space left (extras must be even at this
        // point)
        let weights_len = weights.len();
        for border_i in 0..usize::from(extras / 2) {
            weights[border_i] = weights[border_i].checked_add(1).unwrap();
            let border_opp = weights_len
                .checked_sub(border_i)
                .unwrap()
                .checked_sub(1)
                .unwrap();
            weights[border_opp] = weights[border_opp].checked_add(1).unwrap();
        }

        self.with_weights(weights)
    }

    /// Colors a text.
    ///
    /// # Arguments
    ///
    /// * `foreground_background` - Whether the color is shown on the foreground
    ///   text or the background block
    /// * `space_only` - Whether to only color spaces
    pub fn color_text<S>(
        &self,
        txt: S,
        color_mode: AnsiMode,
        foreground_background: ForegroundBackground,
        space_only: bool,
    ) -> Result<String>
    where
        S: AsRef<str>,
    {
        let txt = txt.as_ref();

        let txt: Vec<&str> = txt.graphemes(true).collect();

        let ColorProfile { colors } = {
            let length = txt.len();
            let length: NonZeroUsize = length.try_into().context("`txt` should not be empty")?;
            let length: NonZeroU8 = length.try_into().with_context(|| {
                format!(
                    "`txt` should not have more than {limit} characters",
                    limit = u8::MAX
                )
            })?;
            self.with_length(length)
                .with_context(|| format!("failed to spread color profile to length {length}"))?
        };

        let mut buf = String::new();
        for (i, &gr) in txt.iter().enumerate() {
            if space_only && gr != " " {
                if i > 0 && txt[i.checked_sub(1).unwrap()] == " " {
                    buf.push_str("\x1b[39;49m");
                }
                buf.push_str(gr);
            } else {
                buf.push_str(&colors[i].to_ansi_string(color_mode, foreground_background));
                buf.push_str(gr);
            }
        }

        buf.push_str("\x1b[39;49m");
        Ok(buf)
    }

    /// Creates a new color profile, with the colors lightened by a multiplier.
    pub fn lighten(&self, multiplier: f32) -> Self {
        let mut rgb_f32_colors: Vec<LinSrgb> =
            self.colors.iter().map(|c| c.into_linear()).collect();

        {
            let okhsl_f32_colors: &mut [Okhsl] = &mut rgb_f32_colors.into_color_mut();

            for okhsl_f32_color in okhsl_f32_colors {
                okhsl_f32_color.lightness *= multiplier;
            }
        }

        let rgb_u8_colors: Vec<_> = rgb_f32_colors
            .into_iter()
            .map(Srgb::<u8>::from_linear)
            .collect();

        Self {
            colors: rgb_u8_colors,
        }
    }

    /// Creates a new color profile, with the colors set to the specified
    /// [`Okhsl`] lightness value.
    pub fn with_lightness(&self, assign_lightness: AssignLightness) -> Self {
        let mut rgb_f32_colors: Vec<LinSrgb> =
            self.colors.iter().map(|c| c.into_linear()).collect();

        {
            let okhsl_f32_colors: &mut [Okhsl] = &mut rgb_f32_colors.into_color_mut();

            for okhsl_f32_color in okhsl_f32_colors {
                match assign_lightness {
                    AssignLightness::Replace(lightness) => {
                        okhsl_f32_color.lightness = lightness.into();
                    },
                    AssignLightness::ClampMax(lightness) => {
                        okhsl_f32_color.lightness.clamp_max_assign(lightness.into());
                    },
                    AssignLightness::ClampMin(lightness) => {
                        okhsl_f32_color.lightness.clamp_min_assign(lightness.into());
                    },
                }
            }
        }

        let rgb_u8_colors: Vec<Srgb<u8>> = rgb_f32_colors
            .into_iter()
            .map(Srgb::<u8>::from_linear)
            .collect();

        Self {
            colors: rgb_u8_colors,
        }
    }

    /// Creates a new color profile, with the colors set to the specified
    /// [`Okhsl`] lightness value, adapted to the terminal theme.
    pub fn with_lightness_adaptive(&self, lightness: Lightness, theme: TerminalTheme) -> Self {
        match theme {
            TerminalTheme::Dark => self.with_lightness(AssignLightness::ClampMin(lightness)),
            TerminalTheme::Light => self.with_lightness(AssignLightness::ClampMax(lightness)),
        }
    }

    /// Creates another color profile with only the unique colors.
    pub fn unique_colors(&self) -> Self {
        let unique_colors: IndexSet<[u8; 3]> = self.colors.iter().map(|&c| c.into()).collect();
        let unique_colors: Vec<Srgb<u8>> = unique_colors.into_iter().map(|c| c.into()).collect();
        Self::new(unique_colors)
    }
}
