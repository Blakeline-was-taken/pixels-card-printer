# pixels-card-printer
This script is used for assembling and exporting playing cards from graphical assets and csv data.
Although I did create a few assets, most graphics were made by these wonderful contributors :
- Pixel Profligate
- Murigen
- Desaft
- Herilind
- Bluemem
- Answearing Machine
- Nevernamed
- syntaxeversion
- Ixams
- Yoyo
- PaperPyro
- NEWS
- Lilith
- Merson
- Synthia
- Omega Shambler
- Prof. Eggnog

More precise credit on the card art is listed in the base cards.csv data files.

# How to install
Before launching anything, launch the `install.bat` file. This will ensure you have all of the required dependencies that the project uses.
Once that's done, you're pretty much good to go! Although, you obviously do need to have python installed for this entire project to work.

# How to use

## Exporting cards, sigils and/or traits
In order to launch the program, simply run the main.py file. Here, you will get to choose what you want to export (cards, sigils or traits), and which of these you want it to generate.

In order to select the items you wish to export, you must enter their name. You can also choose to export an array of items, by putting two names separated by a colon, which will also output every item between the two (in the order they are placed in the data file). For example: `Bullfrog:Cat`

You can export multiple items and arrays of items simply by separating them with commas. For example: `Adder,Bee:Squirrel,Bullfrog,Axolotl:Flying Ant,Wolf:Grizzly,Cat`

Names are case-insensitive but spelling, spaces and special characters do matter.

All exported assets will be placed in their respective folder in the `exports` folder.

**More options for exporting data can be found and changed in the `config.toml` file, such as all the different variants you can export for sigils, what traitline to use for traits, and a LOT of configurable settings for generating cards.**

Among those settings, there is the ability to have icons be used in the sigil descriptions. There are multiple types of icons, and the program will insert them whenever encountering a `[icon_type:value]` tag in a sigil description. Icons are stored in the `assets/icons` folder, except for sigils, which the program automatically takes from the `assets/sigils` folder and rescales to be icons.

There is also the option of exporting sigil patches, that can later be placed on top of cards to add sigils to them in a campaign. You can change the patch image as you see fit, as long as it is named `patch.png` and is located in the `assets` folder.

## Making custom cards
There are two things to do in order to make new cards:

### Adding the raw data
Simply add new rows to the `cards.csv` file (Or replace its rows by your own cards, you do you). If this card uses custom sigils and/or traits, do the same for these in their respective data files.
These files can be found (and have to be located) in the `data` folder.

### Adding the art
You need to add the raw art of your card to the `assets/card_art` folder. It will be pasted on the cardback when generating the card. For custom sigils, also add the sigil image to the `assets/sigils`. If these cannot be colored though (because they already have color in them), be sure to also add the outline of this sigil. Its file name will be the same, with "_outline" at the end.

The files, whether they are card art or sigil art, need to bear the name of the card/sigil but with :
- No spaces
- No special characters in this list : ',-!?

After that, you should be good to go. Although, if you want custom "Conduit" sigils, be sure to also add a conduit indicator image in the folder with the same name located in `assets`. The file will have the exact same name as your sigil image file.

## Adding new icon types
I explained icons earlier, but there is a quick and easy way to add icon types you can toggle on or off based on your preferences.

Basically, all icons except sigils will search their images into the `assets/icons` folder, in which you can add the images you want to use. (they will be scaled to match the sigil description text)

So the only thing you need to do if you want new icon types, is going to the `config.toml` file and adding an icon type under the already existing ones :
```toml
# Icon settings for sigil descriptions
icons.resource = false          # Display resource icons (Default: false)
icons.mark = true               # Display mark icons (Default: true)
icons.sigil = true              # Display sigil icons (Default: true)
icons.YOUR_ICON_TYPE = true     # Display YOUR_ICON_TYPE icons (Default: true)
```

## Making custom temples
You first need to go into the `config.toml` file and add your temple to the list. This will indicate to the program which region to take from sprites containing all temple variants of a certain asset.

Still in the config file, add a text color, a maximum rare height for sigils (it represents how far they can go before overlapping with the border), similarly, a maximum terrain height, the power coordinates (for drawing the power stat) and the attack sigil box (if you want to draw attack sigils atop the attack mark)

Once that is done, you will then need to go through the cardback assets and, for each sprite containing the temple variants of a certain asset, add your temple's variant.
Finally, add the individual bottomless images of your rare card outline (since these can have multiple sizes due to their varying rare outlines, they can't easily be stacked on top of each other), and that should be all you need to have your temple up and running!

## Making custom tiers
Not yet implemented. Just stick to Common, Uncommon, Rare, Side deck and Talking for now.

## Making custom costs
There is currently no way to do it without adding a bit of code to the program yourself. If you're up for that, here is the procedure :

First, the simple part. Add a folder with your costs's name in `assets/costs`, and drop all the graphical assets you will need inside. They will need to be upscaled by 1000% (one pixel becomes a 10x10 pixel).

Second, go into `model/costs.py`. Add a class for your cost, containing an `__init__` method and a `getcostImage(self, temple: str) -> Image` method.

Once these are done, you can go to the bottom of the file and edit the get_cost function. In it, add your own section for recognizing and generating your cost.

The process is similar if you want to edit/add to an already existing cost. Just drop the images you want to use in the cost's asset folder, and edit the cost's class and `get_cost` section.

That's pretty much it, but yeah, you do need to know how to code in python. I will probably add some branches to this repository in order to have other versions of the program with additional costs, but I won't do all of them lmao.
