import os

from PIL import Image, ImageDraw, ImageFont
from model import config

SIGILS = dict()
TRAITS = dict()
SIGIL_IMG_SPACE = config['sigil_img_space']
SIGIL_DESC_SPACE = config['sigil_space'] - 5 - SIGIL_IMG_SPACE
SIGIL_NAME_SIZE = config['sigil_name']
SIGIL_DESCRIPTION_SIZE = config['sigil_description']
TRAIT_DESCRIPTION_SIZE = config['trait_description']
SIGIL_DESC_ICON_SIZE = config['sigil_description_icon_size']
TRAIT_DESC_ICON_SIZE = config['trait_description_icon_size']
FONT = "data/fonts/" + config['font'] + ".ttf"
SIGIL_SCALE = config["sigil_img_scale"] / 100


def get_colon_image(color, size):
    image = Image.new("RGBA", (SIGIL_DESCRIPTION_SIZE, SIGIL_DESCRIPTION_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    heavyweight_font = ImageFont.truetype(FONT, size)
    size = draw.textlength(".", font=heavyweight_font)
    draw.text((0, 0), ".", fill=color, font=heavyweight_font)
    draw.text((0, -size * 2.5), ".", fill=color, font=heavyweight_font)
    return image.crop((0, 0, int(size), SIGIL_DESCRIPTION_SIZE))


def get_resized_image(img, height):
    return img.resize((int(img.width * (height / img.height)), height))


def write_description(x_offset, y_offset, starting_size, description_words, color, text_img, size_limit):
    size = starting_size
    draw = ImageDraw.Draw(text_img)
    heavyweight_font = ImageFont.truetype(FONT, SIGIL_DESCRIPTION_SIZE)

    def add_new_line():
        """Helper function to add a new line to the image."""
        nonlocal y_offset, text_img, draw
        y_offset += SIGIL_DESCRIPTION_SIZE
        new_height = text_img.size[1] + SIGIL_DESCRIPTION_SIZE
        new_img = Image.new("RGBA", (size_limit, new_height), (0, 0, 0, 0))
        new_img.paste(text_img, (0, 0))
        text_img = new_img
        draw = ImageDraw.Draw(text_img)

    def paste_image(image, x_position):
        """Helper function to paste an image at a specific position."""
        text_img.paste(image, (int(x_position), y_offset), image)

    for word in description_words:
        # Handling words with embedded icons
        if "[" in word:
            colon_id = word.index(":")
            icon_type = "sigils" if "sigil" in word else "icons"
            icon_path = f"assets/{icon_type}/{word[colon_id + 1:-1]}.png"
            icon = get_resized_image(Image.open(icon_path), SIGIL_DESC_ICON_SIZE)

            if size + icon.width <= size_limit:
                paste_image(icon, size)
                size += icon.width
            else:
                add_new_line()
                paste_image(icon, x_offset)
                size = x_offset + icon.width

        # Handling colon character
        elif word == ":":
            colon = get_colon_image('black', SIGIL_DESCRIPTION_SIZE)
            if size + colon.width <= size_limit:
                paste_image(colon, size)
                size += colon.width
            else:
                add_new_line()
                paste_image(colon, x_offset)
                size = x_offset + colon.width

        # Handling text words
        else:
            space_word_length = draw.textlength(" " + word, font=heavyweight_font)
            if size + space_word_length <= size_limit:
                draw.text((size, y_offset), " " + word, fill=color, font=heavyweight_font)
                size += space_word_length
            else:
                add_new_line()
                draw.text((x_offset, y_offset), word, fill=color, font=heavyweight_font)
                size = x_offset + draw.textlength(word, font=heavyweight_font)

    return y_offset, text_img


def add_color(image: Image.Image, color):
    for x in range(image.width):
        for y in range(image.height):
            pixel_color = (color[0], color[1], color[2], image.getpixel((x, y))[3])
            image.putpixel((x, y), pixel_color)


class Sigil:

    def __init__(self, name: str, description: str,
                 is_attack_sigil: bool = False, image: Image = None, short_image: Image = None,
                 base_game_image: Image = None, is_trait: bool = False, can_be_colored: bool = True):
        self.name = name
        self.description = description
        self.needs_token = "TOKEN" in description
        self.token = None
        self.is_trait = is_trait
        self.can_be_colored = can_be_colored
        self.image = image
        self.short_image = short_image
        self.base_game_image = base_game_image
        self.is_attack_sigil = is_attack_sigil

    def copy(self):
        return Sigil(self.name, self.description, self.is_attack_sigil, self.image, self.short_image, self.base_game_image, self.is_trait, self.can_be_colored)

    def setToken(self, token: object):
        self.token = token
        self.image = None
        self.short_image = None

    def get_description(self):
        return self.description.replace("TOKEN", str(self.token)) if self.token else self.description

    def sigilImage(self, color='black'):
        name = self.name.translate(str.maketrans("", "", " ',-!?"))
        path = f"assets/sigils/{name}.png"
        if config["show_outline_only"] or (color != "black" and not self.can_be_colored):
            new_path = f"assets/sigils/{name}_outline.png"
            if os.path.exists(new_path):
                path = new_path
        sigil_img = Image.open(path).convert("RGBA")
        sigil_img = sigil_img.resize((round(sigil_img.width * SIGIL_SCALE), round(sigil_img.height * SIGIL_SCALE)))
        if color != 'black':
            add_color(sigil_img, color)
        return sigil_img

    def __draw_base_game(self, sigil_img, color):
        heavyweight_font = ImageFont.truetype(FONT, SIGIL_NAME_SIZE)
        text_img = Image.new("RGBA", (SIGIL_DESC_SPACE, SIGIL_NAME_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        draw.text((0, 0), self.name, fill=color, font=heavyweight_font)

        text_img = text_img.crop((0, 0, round(draw.textlength(self.name, font=heavyweight_font)), SIGIL_NAME_SIZE))
        final_img_width = max(sigil_img.width, text_img.width)
        final_img_height = sigil_img.height + text_img.height + 5
        final_img = Image.new("RGBA", (final_img_width, final_img_height), (0, 0, 0, 0))

        final_img.paste(sigil_img, ((final_img_width - sigil_img.width) // 2, 0))
        final_img.paste(text_img, ((final_img_width - text_img.width) // 2, sigil_img.height + 5))
        return final_img

    def __get_description_words(self):
        description = self.get_description().replace('"', "''").split("[")
        if len(description) > 1:
            desc = [description[0]]
            for item in description[1:]:
                desc += item.split("]")
            description = desc
        description_words = []
        for i in range(len(description)):
            if i % 2 == 0:
                sentences = description[i].split(":")
                for id_sentence in range(len(sentences)):
                    description_words += sentences[id_sentence].split()
                    if len(sentences) > 1 and id_sentence != len(sentences) - 1:
                        description_words += [":"]
            else:
                for icon in config["icons"]:
                    if icon in description[i]:
                        if config["icons"][icon] is True:
                            description_words[-1] += " "
                            description_words.append(f"[{description[i]}]")
                        break
        return description_words

    @staticmethod
    def __get_trait_image(color, description_words):
        size_limit = config['sigil_space'] - 10
        text_img = Image.new("RGBA", (size_limit, TRAIT_DESCRIPTION_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        lengths = [0]
        words_per_phrase = [0]
        heavyweight_font = ImageFont.truetype(FONT, TRAIT_DESCRIPTION_SIZE)

        # Calculate x_offset for each step
        def add_width(width, added_width=None):
            if lengths[-1] + width > size_limit:
                lengths.append(width if added_width is None else added_width)
                words_per_phrase.append(1)
            else:
                lengths[-1] += width
                words_per_phrase[-1] += 1

        for word in description_words:
            if "[" in word:
                colon_id = word.index(":")
                icon_type = "sigils" if "sigil" in word else "icons"
                icon_path = f"assets/{icon_type}/{word[colon_id + 1:-1]}.png"
                icon = get_resized_image(Image.open(icon_path), TRAIT_DESC_ICON_SIZE)
                add_width(icon.width)
            elif word == ":":
                colon = get_colon_image('black', TRAIT_DESCRIPTION_SIZE)
                add_width(colon.width)
            else:
                add_width(draw.textlength(" " + word, font=heavyweight_font),
                          draw.textlength(word, font=heavyweight_font))

        # Write the trait
        x_offset = (text_img.width - lengths[0]) // 2
        y_offset = 0
        word_id = 0

        def add_new_line():
            nonlocal y_offset, text_img
            y_offset += TRAIT_DESCRIPTION_SIZE
            new_height = text_img.size[1] + TRAIT_DESCRIPTION_SIZE
            new_img = Image.new("RGBA", (size_limit, new_height), (0, 0, 0, 0))
            new_img.paste(text_img, (0, 0))
            text_img = new_img

        def add_image(img):
            nonlocal word_id, x_offset, y_offset, text_img
            if word_id >= words_per_phrase[0]:
                add_new_line()
                words_per_phrase.pop(0)
                lengths.pop(0)
                x_offset = (text_img.width - lengths[0]) // 2
                word_id = 0
            text_img.paste(img, (int(x_offset), y_offset), img)
            x_offset += img.width

        for word in description_words:
            if "[" in word:
                colon_id = word.index(":")
                icon_type = "sigils" if "sigil" in word else "icons"
                icon_path = f"assets/{icon_type}/{word[colon_id + 1:-1]}.png"
                icon = get_resized_image(Image.open(icon_path), TRAIT_DESC_ICON_SIZE)
                if color != 'black':
                    add_color(icon, color)
                add_image(icon)
            elif word == ":":
                colon = get_colon_image('black', TRAIT_DESCRIPTION_SIZE)
                if color != 'black':
                    add_color(colon, color)
                add_image(colon)
            elif word_id < words_per_phrase[0]:
                draw.text((x_offset, y_offset), " " + word, fill=color, font=heavyweight_font)
                x_offset += draw.textlength(" " + word, font=heavyweight_font)
            else:
                words_per_phrase.pop(0)
                lengths.pop(0)
                x_offset = (text_img.width - lengths[0]) // 2
                word_id = 0

                add_new_line()

                draw = ImageDraw.Draw(text_img)
                draw.text((x_offset, y_offset), word, fill=color, font=heavyweight_font)
                x_offset += draw.textlength(word, font=heavyweight_font)
            word_id += 1
        return text_img

    def getImage(self, color='black', base_game: bool = False, shortened_format: bool = False):
        if base_game and self.base_game_image:
            return self.base_game_image
        if shortened_format and self.short_image:
            return self.short_image
        if not base_game and not shortened_format and self.image:
            return self.image

        if not self.is_trait:
            sigil_img = self.sigilImage(color)

        if base_game:
            if self.is_trait:
                self.base_game_image = Image.new("RGBA", (0, 0))
            else:
                # Draw sigil using base game aesthetic
                self.base_game_image = self.__draw_base_game(sigil_img, color)
            return self.base_game_image

        description_words = self.__get_description_words()

        if self.is_trait:
            self.image = self.__get_trait_image(color, description_words)
            self.base_game_image = self.image
            return self.image

        heavyweight_font = ImageFont.truetype(FONT, SIGIL_NAME_SIZE)
        text_img = Image.new("RGBA", (SIGIL_DESC_SPACE, SIGIL_NAME_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        size = round(draw.textlength(self.name, font=heavyweight_font))
        draw.text((0, 0), self.name, fill=color, font=heavyweight_font)
        if shortened_format:
            # Draw sigil using shortened formatting

            colon = get_colon_image(color, SIGIL_NAME_SIZE)
            text_img.paste(colon, (size, 0), colon)
            size += colon.width

            y_offset, text_img = write_description(0, SIGIL_NAME_SIZE - SIGIL_DESCRIPTION_SIZE - 1,
                                                   size, description_words, color,
                                                   text_img, SIGIL_DESC_SPACE)
        else:
            # Draw sigil normally

            new_height = text_img.size[1] + SIGIL_NAME_SIZE
            new_img = Image.new("RGBA", (SIGIL_DESC_SPACE, new_height), (0, 0, 0, 0))
            new_img.paste(text_img, (0, 0))
            text_img = new_img
            draw = ImageDraw.Draw(text_img)
            heavyweight_font = ImageFont.truetype(FONT, SIGIL_DESCRIPTION_SIZE)
            size = SIGIL_DESCRIPTION_SIZE

            # We have to draw the first word because for some reason otherwise the first line is offset from the others.
            if not ("[" in description_words[0]):
                first_word = description_words.pop(0)
                draw.text((size, SIGIL_NAME_SIZE), first_word, fill=color, font=heavyweight_font)
                size += draw.textlength(first_word, font=heavyweight_font)

            y_offset, text_img = write_description(SIGIL_DESCRIPTION_SIZE, SIGIL_NAME_SIZE,
                                                   size, description_words, color,
                                                   text_img, SIGIL_DESC_SPACE)

        text_height = y_offset + SIGIL_DESCRIPTION_SIZE
        final_img_height = max(text_height, sigil_img.height)
        final_img = Image.new("RGBA", (config['sigil_space'], final_img_height), (0, 0, 0, 0))
        final_img.paste(sigil_img,
                        ((SIGIL_IMG_SPACE - sigil_img.width) // 2,
                         min((final_img_height - sigil_img.height) // 2, 10)))
        final_img.paste(text_img.crop((0, 0, text_img.width, text_height)),
                        (SIGIL_IMG_SPACE, (final_img_height - text_height) // 2))
        if shortened_format:
            self.short_image = final_img
        else:
            self.image = final_img
        return final_img


def add_sigil(csv_dict):
    global SIGILS
    is_attack_sigil = csv_dict['Is_attack_sigil'] in ['True', 'T', 't', 'y', 'Y', 'Yes']
    SIGILS[csv_dict['Name']] = Sigil(csv_dict["Name"],
                                     csv_dict["Description"],
                                     is_attack_sigil,
                                     can_be_colored=csv_dict["Can_be_colored"] in ['True', 'T', 't', 'y', 'Y', 'Yes'])
    if (is_attack_sigil and config["attack_sigil_on_power_stat"]) or \
            (csv_dict["Name"] == "Bloodless" and config["bloodless_sigil_to_trait"]):
        add_trait(csv_dict)


def add_trait(csv_dict):
    global TRAITS
    TRAITS[csv_dict['Name']] = Sigil(csv_dict["Name"],
                                     csv_dict["Description"],
                                     csv_dict['Is_attack_sigil'] in ['True', 'T', 't', 'y', 'Y', 'Yes'],
                                     is_trait=True)
