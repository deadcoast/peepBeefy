# ASCII RESEARCH

Many might have heard of terms like 'ASCII art' or 'ANSi art'. But before we dig into details, let's take a closer look at how computers screens in the early 80’s were displaying text and images.
It might now be hard to imagine, but there was a time where we had to do without any real Graphical User Interface (GUI). Before the Macintosh, Amiga Workbench, Atari's GEM and (arguably) Windows were available, computers screens were mostly limited by 'text mode' only.
In text mode the display is divided into 25 rows and 80 columns in order to display text without images. And each box can contain **one** character. Text mode is also known as character mode or alphanumeric mode.
Early 60’s telegraph code was used as a basis for what later became the ASCII *(American Standard Code for Information Interchange)* character encoding standard. Because of technical limitations of computer systems at the time, it provided only 7-bits (128 characters) of which [only 95 were printable characters](https://en.wikipedia.org/wiki/ASCII#Printable_characters).

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*RvlObPIDmwc1IqRyPVCFuQ.png)

## The OG ASCII table from a pre-1972 printer manual

> Some of the control characters, mainly used for printers in mind, are still used until this very day. Like the carriage return `\r` and line feed `\n` symbols.

### Code page 437

When IBM shipped its first "Personal Computer" in 1981 it came standard with a character set 'code page 437' also known as CP437, OEM-US, OEM 437, PC-8, or DOS Latin US. This 9x14 pixels-per-character font was stored in the ROM of the [monochrome display adapter](https://en.wikipedia.org/wiki/IBM_Monochrome_Display_Adapter).
The set includes all printable ASCII characters as well as some accented letters, Greek letters, icons, and line-drawing symbols. It is sometimes referred to as the “OEM font”, “high ASCII” or “ [extended ASCII](https://en.wikipedia.org/wiki/Extended_ASCII) ”.
This character set remains the primary set in the core of any [EGA](https://en.wikipedia.org/wiki/Enhanced_Graphics_Adapter) and [VGA](https://en.wikipedia.org/wiki/Video_Graphics_Array) -compatible graphics card. As such, text shown when a PC reboots (before fonts can be loaded and rendered) is typically rendered using this character set.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*mPyXehrofqWEpYaxW7TRQQ.png)

IBM's code page 437

The example above also shows rectangular and square block in four different shades. When the Color Graphics Adapter (CGA) was released these could be combined with 16 colors. This became the bases of "ANSi art" as we know it today.

> Technically ASCII art refers to artwork that consist of only the 95 printable characters of the original ASCII chart. Where ANSi art refers to artwork created with all of the 223 characters available in the "extended ASCII" version. ANSi art also contains special [ANSi escape sequences](https://en.wikipedia.org/wiki/ANSI_escape_code) that color text with the 16 foreground and 8 background colors. On an MS-DOS device this was offered by [ANSI.SYS](https://en.wikipedia.org/wiki/ANSI.SYS), a [device driver](https://en.wikipedia.org/wiki/Device_driver) loosely based upon the [ANSI](https://en.wikipedia.org/wiki/American_National_Standards_Institute) X3.64 standard which was added as a line in the `[CONFIG.SYS](https://en.wikipedia.org/wiki/CONFIG.SYS)` in DOS.

```c
DEVICE=C:\DOS\ANSI.SYS
```

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*SSzQx0rg0R8b40QY2OYh8g.png)

Weekly comic submission comic.browserling.com illustrating the difference between standard ASCII art and ANSi art perfectly

### Early GUI's

This extended list of characters provided a way to create early GUI's:

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*tEhdbIujhjXtPta7MNPTYQ.png)

Early graphical user-interface made with extended ASCII characters

And this approach is still be visible today on modern systems:

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*gED7IRAzaa63MvPT5NTzNQ.png)

Ubuntu 22 upgrade screens today still make use of ASCII characters and colors to make things prettier.

## BBS

What kickstarted the whole "ANSi" scene was the rise of BBSes. A Bulletin Board Service is a computer running software to which users could connect directly over their telephone lines.

Once logged in, the user could perform functions such as downloading/uploading software, reading news, posting bulletins and exchanging messages with other users through public message boards. In the early 1980s, message networks such as [FidoNet](https://en.wikipedia.org/wiki/FidoNet) were developed to provide services such as NetMail, which is similar to internet-based e-mail we use today. BBSes with multiple phone lines often provided chat rooms.

Bulletin Board Systems were in many ways a precursor to the modern-day Internet and social networks. Low-cost, high-performance modems drove the use of BBSes through the early 1990s.

### Phone bill

My earliest memory of using a BBS myself, is after I got stuck during playing one of my favorite adventure games at the time by Sierra On-line.

These games were brutal by todays standards! because you could have missed picking up a very important item earlier in the game, which you needed later on. That's why you had to create lots of saved games so that you were able to backtrack to earlier states of your playthrough.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*eHcUExDIqKnWHgmo-OZyvw.png)

Leisure Suit Larry by Sierra On-line released in 1987
Sierra On-line advertised their BBS on the retail boxes and inside game manuals. *(which were sometimes carefully copied from the original 🏴☠️)* These would provide hints and solutions for the many challenges you had to overcome playing their games.
I figured out that by pulling the telephone line from the fax machine next to the computer, and sticking it into the modem, I could connect to the BBS without our home phone calls being interrupted in any way. 😇
Little did I know that I was making expensive long distance international phone calls, which caused very unusual bills for a fax machine… 🙄

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*NaCxlTOUmqQl0-1o0W-QWg.png)

Screenshot of Sierra On-Line BBS

Everybody who remembers the dial-up period knows how frustrating it was when somebody else in the house started using the phone in the middle of a download you were waiting for to complete for over 20 minutes.

> “MOOOOM, DON’T PICK UP THE PHONE!”

## Release groups and demo scene

The rise of the ANSi scene came most directly by the underground already in place which was illegally pirating software, most commonly known as `warez`.

Kids in the 80s had a bigger apetite for playing video games than their budgets would allow. So they started sharing games with each other. Software developers noticed this and tried implementing all kinds of copy protection to prevent this. Hackers became familiar with the programming languages used by the developers and found elaborate ways to work around them and released 'cracked' games. Sometimes even before these games hit the store shelves (`0-day warez`).

Pirate groups were formed all over the world and a massive rivalry started which group could get their hands on new games, and crack the copy protection first. They applied their signatures to these games in the form of opening screens with artwork, or later more elaborate animations with sounds and music, to brag about their accomplishments. These intros are also known as a " *cracktro* ".

> This groups of hackers and crackers called themselves "elite" (`3l33t` or `1337`) and started applying different spelling in their language, known as " [leetspeak](https://en.wikipedia.org/wiki/Leet) ". Some words (i.e. n00b or pwnd) are still found in common Internet usage.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*T2OLLZNOISNYH1cmVgMZZA.png)

Groups like Fairlight, Razor1911 and ACiD were amongst the most popular release groups

### Fighting for (floppy) space

Quickly the artists discovered ways to scroll their art across the screen to expand their 80x25 canvas limitations. And by adding music (mostly in a `MOD` format) these intros quickly became larger and larger.

A one megabyte file was still very large to transfer over a phone line, and a high-density floppy disk could only store 1,44 megabytes of data. That's why some release groups started to release their artwork without any game at all. This became known as a 'demo' and the 'demo scene' started.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*4LhnpRVbak99nV_Z4o3k2w.gif)

multi-screen ANSi made by sensei from the Acid group in 1996

### The Art of Warez

If you want to learn more about the rise (and fall) of ANSi and the demo scene, I would **highly** suggest watching the (30 min.) [documentary ***"Safe Crackers: The Art of Warez"*** on YouTube](https://www.youtube.com/watch?v=Yd-s9htpHgQ&t=3s).

> A combination of techniques and the full embrace of the low resolution colored block, as a possibility for abstraction and expression rather than simply a limitation of illustrative realism, led to aesthetics which would have not been seen before in other art forms.
>
> — Kevin Bouton-Scott, The Art of Warez

### Demo parties

All over the world large LAN parties were organized and the biger ones also had a specific focus on the demo scene. Demo groups or individual artist were painfully crafting their newest artworks during the weekend, one character at a time…

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*fMKe-Nh3pZdJeYJccW-aIA.jpeg)

Demo- and LAN party "Assembly" in Helsinki, Finland

During the weekend there were usually several moments for visitors to vote their pick in several different categories.

I was visiting "Takeover" in 2001 where there were still large groups op people bringing their Amiga's and musical instruments to compete into several of the artist competitions.

> These weekends generally started on Fridays and continued non-stop until Sunday. I was surviving on pizza, soda, the adrenaline of playing multiplayer Quake and a few hours of sleep next to my desktop (full tower!) or in the car on the parking lot. Aaah,… those were the days…. 😊

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*a8HlNhBFseL8Vj90HCnPrw.jpeg)

LAN/demo party "Takeover" in 2001 hosted at the Technical University in Eindhoven, The Netherlands

> I can remember clearly that some of these demos were truly amazing to watch! Especially in the 90s when graphics cards weren't powerful enough to render 3D in real-time. Some of the demos seemed to create animations impossible to run on current hardware. And the filesizes were tiny!

## View and create ANSi art

During the 90s several tools arose with which manipulating ASCII characters and colors was made much easier. With hotkeys for frequently used actions and mouse support for moving, copying and pasting sections of characters. Release group ACiD released their own tool called [ACiDDraw and it can still be downloaded of their website](https://www.acid.org/apps/apps.html).

With today's hardware you'll need to resort to DOSbox for running these pieces of software or use a more modern application like [PabloDraw](https://picoe.ca/products/pablodraw/) or [Moebius](https://blocktronics.github.io/moebius/).

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*NgzDItS4IJVk3zdt_WFQ1Q.png)

Moebius is a modern-day ANSI viewer/editor available for MacOS, Windows and Linux

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*UWYFiCwJimK9hvCK7V1NGg.png)

PabloDraw automatically connects to the Sixteen Colors database where a lot of ANSi is preserved.

## Uses in the modern day

Modern operating systems have access to a more elaborate text encoding standard named **Unicode**. As of the current version (15.0) it consists of almost 150.000 characters covering 161 modern and historic [scripts](https://en.wikipedia.org/wiki/Script_\(Unicode\)) *(i.e. Arabic and Egyptian hieroglyphs)* as well as lots of symbols and [emoji’s](https://unicode.org/emoji/charts/full-emoji-list.html).
The Unicode standard is maintained by the [Unicode Consortium](https://en.wikipedia.org/wiki/Unicode_Consortium), a non-profit organization which includes most of the main computer companies with any interest in text-processing standards. Including Adobe, Apple, Google, IBM, Microsoft, and SAP.
Although ANSi and BBSes were both rendered obsolete by the rise of the Internet, and increased speed capacities of our digital connections, there are still people out there keeping this art form alive until this very day!

### Internet-based BBS

A couple of modern BBSes can be accessed with a telnet client over the Internet. Most require some specific terminal settings (such as line spacing) for optimal results of the artworks. Some of them will also have the ability to visit the BBS from a web browser or a dedicated telnet client with RIP.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*Uwuunu2X2e-3FbZaXAEhTA.png)

ACiD still has an active BBS called "ACiD Underworld"

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*OIrdyZ76t_MyGXk-sIdJEw.png)

The Realm of Serion

### RIP

No, not rest in piece but [Remote Imaging Protocol](https://en.wikipedia.org/wiki/Remote_Imaging_Protocol). It's a technology which was new to me, but I encountered during the research for this article.

With RIP more sophisticated vector graphics can be used over low-bandwidth links. Apparently this isn't something new since it's been around since 1992. Also RIP-capable clients and servers provide the option to use graphical menus which can be controlled by mouse input.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*giCQFQwosYMr8pHzio2a9Q.png)

Black Flag Acid BBS showcasing RIP graphics drawn by fine lines, and mouse support

Upon logging into the ACiD underworld I was greeted by "Hawk Hubbard" via a private chat to my great surprise! He appeared to be the operator keeping the BBS online!

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*nARtVdr-CjODHE0AypNiWw.png)

My conversation with 'Hawk Hubbard' who's keeping the "ACiD underworld" (blackflag) BBS online

### New ANSI packs

I was also surprised to learn that new ANSi packs are still released until this very day. Websites like [Sixteen Colors](https://16colo.rs/) and [Bricktronics](http://blocktronics.org/) provide galleries of old and new works of art.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*FcJevAsgo-u-QLjjrFZlJQ.png)

Artwork created by Mr.R0b070 in 2022

### Star Wars in ASCII

**Fun fact!** You can watch the entire first Star Wars movie "A New Hope" in ASCII!

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*R90Yf65y89CAKHjZuLNNPg.png)

Han shot first!!

This project started in 1997 and is still online until this very day! You can watch it by connecting with `telnet` or [in your webbrowser](http://www.asciimation.co.nz/index.php).

```c
telnet towel.blinkenlights.nl
```

If you're interested in more background information, also check out [their FAQ section](http://www.asciimation.co.nz/asciimation/ascii_faq.html).

## Back to the future

Yes, back in 2022 again ready to close the year and start off with a new one.

I promised in my title and introduction to elaborate a bit on how you can take some of that 80s and 90s ANSi nostalgia, and apply it into your daily work today. Well, here are a couple of tips.

### Generate ASCII/ANSI yourself

It's obviously not possible to just easily generate some full-screen artwork, but there are some options to create some nice looking logo's for example.

With FIGlet you can provide a string (and optionally a font) and it will output a logo with ASCII characters. These can be copy/pasted or stored in a file to display. For example when you run a script or login to a shell.

[FIGlet](https://en.wikipedia.org/wiki/FIGlet) is available since 1991 and [can still be downloaded](http://www.figlet.org/) and used on several different operating systems. There's also an option to [download and install additional "fonts"](https://github.com/xero/figlet-fonts).

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*YCddZs3HQcLVyuKewOqtMA.png)

A few examples of FIGlet fonts

> If you want to try it out the easiest way is to [visit this website](https://patorjk.com/software/taag/#p=testall&f=3D%20Diagonal&t=ANSi).  
> Type in a string and click on the "test all" button.

FIGlet will only output plain ASCII, without any ANSi control characters to display colors for example. But with the help of `lolcat` (an utility for Linux, BSD and OSX) you can add some color! 🎨

Lolcat concatenates similarly to the `cat` command and adds rainbow coloring to it. 🌈 You can simply add `| lolcat` to anything to colorize it!

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*k0HguGk8fD8oM5KdIY1gRQ.png)

'ls' with some flair

And this in turn can be combined with FIGlet to create colorized logo's!

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*ZuJxY6IhrPyYK4cpUMtblw.png)

And the nice thing is, is that the color information can be saved as ANSi into a text file for later use.

```c
figlet "I love rainbows" | lolcat -f -p 1.5 >> ~/rainbow.ans
```

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*k2DMNHEGuScFtz8fhtZpbw.png)

the contents of rainbow.ans showing ANSi control characters for color encoding

You can combine this for example with other tools like [NeoFetch](https://github.com/dylanaraps/neofetch) to create some nice looking login screens for example. 😎

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*On_VJRqyI6eg-dbZl1K0_Q.png)

Your ' message of the day ' never looked this good!

If you want to see how this was made, and try it out yourself, check out [my Github repository](https://github.com/TheCloudScout/linux-asnsi-login) and download and run `ascii-header-install.sh`.

### Get your (Power)Shell "poshed" up

That's all fun and all when you're running Linux, but Windows users: I've got something for you as well.

**Install Oh My Posh  
**PowerShell users really need to look into [installing oh-my-posh](https://ohmyposh.dev/docs/installation/windows). It not only looks nicer than your default shell, it's also useful by displaying statues about the things you're currently working on.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*WsNI1rzZdfrYrsfAM8NaeQ.png)

Oh-my-posh showing me the actual Git status on the command line

There a [loads of themes available](https://ohmyposh.dev/docs/themes), so choose whatever you like most. After installation you need to add it to your profile so that it always runs upon opening:

```c
code $profile
```

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*jvOYD3k5TJqIMP3vMcxWzQ.png)

I'm fond of the "marcduiker" theme together with some other 'quality of life' improvements for PowerShell

### Nerd fonts?

And lastly I'd like to point out "nerd fonts". *(yes, that's really how they're supposed to be called)* These fonts are a collection of modified fonts aimed at developers. They're "monospaced", which means that the spacing of characters is always the same for every character so that they line up nicely. Most fonts are extended by adding extra 'glyphs' and ' [ligatures](https://en.wikipedia.org/wiki/Ligature_\(writing\)) '.

> These 'glyphs' are the little icons you'll see in a lot of oh-my-posh theme examples. And 'ligatures' are multiple characted placed against each other to form different shapes or symbols. A fine example of [a font with nice 'ligatures' is FireCode](https://github.com/tonsky/FiraCode), which I used as default in VScode.

According to [the FireCode devs](https://github.com/tonsky/FiraCode):

> Programmers use a lot of symbols, often encoded with several characters. For the human brain, sequences like `->`, `<=` or `:=` are single logical tokens, even if they take two or three characters on the screen. Your eye spends a non-zero amount of energy to scan, parse and join multiple characters into a single logical one. Ideally, all programming languages should be designed with full-fledged Unicode symbols for operators, but that’s not the case yet.
>
> Fira Code is a free monospaced font containing ligatures for common programming multi-character combinations. This is just a font rendering feature: underlying code remains ASCII-compatible. This helps to read and understand code faster. For some frequent sequences like `..` or `//`, ligatures allow us to correct spacing.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*luyQcM8HPlWkjZ2SSNl1rA.png)

Example of 'ligatures' which make your code prettier and easier to read

---
