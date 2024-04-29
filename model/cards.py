from PIL import Image, ImageDraw, ImageFont
from model import config, logging, sigils, costs
from unidecode import unidecode

TEMPLES = config['temples']
TEXT_COLORS = config['text_colors']
FONT = "data/fonts/" + config['font'] + ".ttf"


def get_bottom_outline_y(tier, temple, bloodless):
    bloodless = bloodless and config["bloodless_outline"]
    if tier in ["Common", "Side Deck", "Talking"]:
        return config['max_common_height'] if (bloodless is False) else config['max_common_terrain_height']
    if tier == "Uncommon":
        return config['max_uncommon_height'] if (bloodless is False) else config['max_uncommon_terrain_height']
    if tier == "Rare":
        if bloodless is False:
            return config['max_rare_height'].get(temple, config['max_common_height'])
        return config['max_rare_terrain_height'].get(temple, config['max_common_terrain_height'])
    else:
        print(f"Error: Tier not recognized : {tier}")
        logging.error(f"Error: Tier not recognized : {tier}")


def format_evaluation(sigil_list, trait_list, sigil_y, image, tier, temple, bloodless, default_format: bool = True):
    can_draw_sigils = True
    # Add the combined height of all the sigils.
    for sigil in sigil_list:
        sigil_img = sigil.getImage() if default_format else sigil.getImage(shortened_format=True)
        # If the sigil height overflows the card, we can't draw the sigils.
        if sigil_y + sigil_img.height > image.height:
            can_draw_sigils = False
        sigil_y += sigil_img.height + 5
    trait_height = 0
    if len(trait_list) > 0:
        traitlines = Image.open(f"assets/cardbacks/Traitlines.png")
        traitline = costs.get_temple_variant(traitlines, temple)
        trait_height = traitline.height * 10 + 6
    for trait in trait_list:
        trait_img = trait.getImage(color=TEXT_COLORS[temple])
        # If the trait height overflows the card, we can't draw the sigils.
        if sigil_y + trait_height + trait_img.height > image.height:
            can_draw_sigils = False
        trait_height += trait_img.height
    sigil_y += trait_height
    # If the sigil height does not overflow the card, but is on top of the bottom border of the image,
    # then we need to use the empty bottom for this card.
    use_empty_bottom = sigil_y > get_bottom_outline_y(tier, temple, bloodless)
    return can_draw_sigils, use_empty_bottom, trait_height


def paste_card_art(name, image, cost, temple):
    # Fetch card art and paste it
    card_art = None
    image_file = name.translate(str.maketrans("", "", " ',-!?"))
    if "_alt" in name:
        try:
            card_art = Image.open(f"assets/card_art/{image_file}-alt.png").convert("RGBA")
        except FileNotFoundError:
            try:
                card_art = Image.open(f"assets/card_art/{image_file}.png").convert("RGBA")
            except FileNotFoundError:
                print(f"Error: assets/card_art/{image_file}.png file not found.")
                logging.error(f"Error: assets/card_art/{image_file}.png file not found.")
    if not card_art:
        card_art = Image.open(f"assets/card_art/{image_file}.png").convert("RGBA")
        card_art = card_art.resize((card_art.width * 10, card_art.height * 10), Image.NEAREST)
    image.paste(card_art, mask=card_art)

    # Generate and paste cost
    cost_y = config['cost_bottom']
    for cost in cost:
        cost_img = cost.getCostImage(temple)
        cost_y -= cost_img.height + 10
        image.paste(cost_img, (config['cost_right_border'] - cost_img.width, cost_y), cost_img)


def paste_sigil(image, sigil_img, box):
    sigil_img_trans = Image.new("RGBA", image.size)
    sigil_img_trans.paste(sigil_img, box, mask=sigil_img)
    new_img = Image.alpha_composite(image, sigil_img_trans)
    return new_img


def get_sigil_and_trait_list(csv_dict, conduit):
    str_sigils = csv_dict['Sigils'].split(', ') if csv_dict['Sigils'] not in ['None', ''] else []
    str_tokens = csv_dict['Token'].split(', ') if csv_dict['Token'] not in ['None', ''] else []
    str_traits = csv_dict['Traits'].split(', ') if csv_dict['Traits'] not in ['None', ''] else []
    has_attack_sigil = False
    token_id = 0

    def handle_sigil_or_trait(att_list, att_dict, tokens, tok_id):
        att_list.append(att_dict[sigil].copy())
        if att_list[-1].needs_token:
            att_list[-1].setToken(tokens[tok_id % len(tokens)])
            tok_id += 1
        return att_list[-1].is_attack_sigil

    sigil_list = []
    trait_list = []

    try:
        for sigil in str_sigils:
            if sigil in sigils.TRAITS and not (sigil == "Bloodless" and not config["show_bloodless_text"]):
                if handle_sigil_or_trait(trait_list, sigils.TRAITS, str_tokens, token_id):
                    has_attack_sigil = True

            elif sigil in sigils.SIGILS and not (sigil == "Bloodless" and not config["show_bloodless_text"]):
                if handle_sigil_or_trait(sigil_list, sigils.SIGILS, str_tokens, token_id):
                    has_attack_sigil = True
                # Determine if a conduit indicator will need to be on the card because of a Conduit sigil.
                if "Conduit" in sigil:
                    if not (conduit and sigil == "Null Conduit"):
                        conduit = sigil.translate(str.maketrans("", "", " ',-!?"))

        for sigil in str_traits:
            if sigil in sigils.TRAITS and not (sigil == "Bloodless" and not config["show_bloodless_text"]):
                if handle_sigil_or_trait(trait_list, sigils.TRAITS, str_tokens, token_id):
                    has_attack_sigil = True

        return sigil_list, trait_list, has_attack_sigil, conduit
    except KeyError as e:
        print(f"Error: {e}")
        logging.error(f"Error: {e}")


def write_name(image, draw, name):
    written_name = unidecode(name).replace("_alt", "")
    name_size = config['name']
    name_y = config['card_name_top_height']
    heavyweight_font = ImageFont.truetype(FONT, name_size)
    while draw.textlength(written_name, font=heavyweight_font) > config['max_name_width']:
        name_size -= 1
        heavyweight_font = ImageFont.truetype(FONT, name_size)
        name_y += 0.5
    if config["center_card_name"]:
        name_x = (image.width - draw.textlength(written_name, font=heavyweight_font)) // 2
    else:
        name_x = config["card_name_left_border"]
    draw.text((name_x, int(name_y)), written_name, fill="black", font=heavyweight_font)


def write_flavor_text(draw, font, flavor_text, temple):
    flavor_text: str = flavor_text.replace("\r", "").replace("\n", " ").replace('"', "''")
    if flavor_text != "BLANK":
        while draw.textlength(flavor_text, font=font) > config['max_flavor_text_width']:
            limit = flavor_text.rfind(" ") if " " in flavor_text else -6
            flavor_text = flavor_text[:limit] + "..."
            flavor_text += "''" if "''" in flavor_text else ""
        flavor_text_x = 300 + (700 - draw.textlength(flavor_text, font=font)) // 2
        draw.text((flavor_text_x, config['flavor_text_top_height']), flavor_text, fill=TEXT_COLORS[temple],
                  font=font)


def write_card_description(image, draw, font, temple, tier, tribes):
    description = f"{tier} {temple}"
    if len(tribes) > 0:
        description += " - "
        for tribe in tribes:
            description += tribe + " "
        description = description[:-1]
    desc_y = config['description_top_height']
    desc_x = (image.width - draw.textlength(description, font=font)) // 2
    draw.text((desc_x, desc_y), description, fill=TEXT_COLORS[temple], font=font)


def draw_text(image, name, tier, temple, tribes, flavor_text):
    draw = ImageDraw.Draw(image)
    heavyweight_font = ImageFont.truetype(FONT, config['flavor_text'])

    # Write card name
    write_name(image, draw, name)

    # Write flavor text
    write_flavor_text(draw, heavyweight_font, flavor_text, temple)

    # Write tribes, tier and temple
    if config["write_card_description"]:
        write_card_description(image, draw, heavyweight_font, temple, tier, tribes)


def draw_conduit_indicator(image, conduit_img):
    conduit_x = (image.width - conduit_img.width) // 2
    image = paste_sigil(image, conduit_img, (conduit_x, config['conduit_top_height']))
    return image


def draw_sigils(image, temple, tier, file_tier, sac, bloodless,
                conduit, conduit_img, sigil_y, sigil_list, trait_list, default_format):
    can_draw_sigils, use_empty_bottom, trait_height = format_evaluation(
        sigil_list, trait_list, sigil_y, image, tier, temple, bloodless, default_format
    )

    if use_empty_bottom:
        if not config["allow_card_bottom_removal"]:
            can_draw_sigils = False
        elif not config["prioritize_removing_bottom"] and default_format:
            can_draw_sigils = False
    if can_draw_sigils or not (default_format or config["allow_base_game_display"]):
        can_draw_sigils = True

        if use_empty_bottom:
            try:
                if tier != "Rare":
                    img_path = f"assets/cardbacks/{file_tier}{sac}Cardback_bt.png"
                    img = Image.open(img_path).convert("RGBA")
                    bottom_image = costs.get_temple_variant(img, temple)
                    bottom_image = bottom_image.resize((bottom_image.width * 10, bottom_image.height * 10), Image.NEAREST)
                else:
                    bottom_image = Image.open(f"assets/cardbacks/{file_tier}{temple}{sac}Cardback_bt.png")
                    bottom_image = bottom_image.resize((bottom_image.width * 10, bottom_image.height * 10), Image.NEAREST)
                image.paste(bottom_image, (0, image.height - bottom_image.height), bottom_image)
            except FileNotFoundError:
                print(f"Error: assets/cardbacks/{file_tier}{temple}{sac}_bt.png image not found.")
                logging.error(f"Error: assets/cardbacks/{file_tier}{temple}{sac}_bt.png image not found.")
                return

        if conduit:
            # We draw the conduit indicator on the image.
            image = draw_conduit_indicator(image, conduit_img)

        # Draw each sigil on the card
        for sigil in sigil_list:
            sigil_img = sigil.getImage() if default_format else sigil.getImage(shortened_format=True)
            image = paste_sigil(image, sigil_img, (config['sigil_left_border'], sigil_y))
            sigil_y += sigil_img.height + 5

        if len(trait_list) > 0:
            try:
                traitlines = Image.open(f"assets/cardbacks/Traitlines.png")
                traitline = costs.get_temple_variant(traitlines, temple)
            except FileNotFoundError:
                print(f"Error: assets/cardbacks/Traitlines.png image not found.")
                logging.error(f"Error: assets/cardbacks/Traitlines.png image not found.")
                return
            traitline = traitline.resize((traitline.width * 10, traitline.height * 10), Image.NEAREST)
            traitline_x = (image.width - traitline.width) // 2
            traitline_x -= traitline_x % 10
            if config["traits_at_bottom"] and not use_empty_bottom:
                traitline_y = get_bottom_outline_y(tier, temple, bloodless) - trait_height
                traitline_y -= (traitline_y % 10)
            else:
                traitline_y = sigil_y - (sigil_y % 10) + 10
            sigil_y = traitline_y + traitline.height + 6
            image.paste(traitline, (traitline_x, traitline_y), traitline)

        for trait in trait_list:
            trait_img = trait.getImage(color=TEXT_COLORS[temple])
            image = paste_sigil(image, trait_img, (config['sigil_left_border'], sigil_y))
            sigil_y += trait_img.height
            if trait.is_attack_sigil:
                attack_sigil = trait.sigilImage()
                attack_box = config["attack_sigil_box"].get(temple if not bloodless else 'Terrain')

                box_x = attack_box[0] + ((attack_box[2] - attack_box[0]) - attack_sigil.width) // 2
                box_y = attack_box[1] + ((attack_box[3] - attack_box[1]) - attack_sigil.height) // 2
                image = paste_sigil(image, attack_sigil, (box_x, box_y))
    return can_draw_sigils, image


def draw_base_game_display(image, conduit, conduit_img, sigil_list):
    if conduit:
        # We draw the conduit indicator on the image.
        image = draw_conduit_indicator(image, conduit_img)

    if 0 < len(sigil_list) < 3:
        left_border = config['sigil_left_border']
        size = config['sigil_space'] // len(sigil_list)
        sigil_y = (config['sigil_top_height'] + config['sigil_lower_top_height']) // 2
        for sigil in sigil_list:
            sigil_img = sigil.getImage(base_game=True)
            sigil_x = left_border + (size - sigil_img.width) // 2
            image = paste_sigil(image, sigil_img, (sigil_x, sigil_y))
            left_border += size
    elif len(sigil_list) > 0:
        sigils_lower_half = int(len(sigil_list) / 2)
        sigils_upper_half = sigils_lower_half
        if sigils_lower_half != len(sigil_list) / 2:
            sigils_upper_half += 1

        left_border = config['sigil_left_border']
        size = config['sigil_space'] // sigils_upper_half
        for sigil in sigil_list[:sigils_upper_half]:
            sigil_img = sigil.getImage(base_game=True)
            sigil_x = left_border + (size - sigil_img.width) // 2
            image = paste_sigil(image, sigil_img, (sigil_x, config['sigil_top_height']))
            left_border += size

        left_border = config['sigil_left_border']
        size = config['sigil_space'] // sigils_lower_half
        for sigil in sigil_list[sigils_upper_half:]:
            sigil_img = sigil.getImage(base_game=True)
            sigil_x = left_border + (size - sigil_img.width) // 2
            image = paste_sigil(image, sigil_img, (sigil_x, config['sigil_lower_top_height']))
            left_border += size
    return image


def create_card(csv_dict):
    global TEMPLES, TEXT_COLORS
    # Load data
    bloodless = ('Bloodless' in csv_dict['Sigils'] or 'Bloodless' in csv_dict['Traits']) and config['bloodless_outline']
    sac = "Terrain" if bloodless else ""
    tier = csv_dict['Tier']
    file_tier = tier if tier != "Side Deck" else "Common"
    temple = csv_dict['Temple']

    # Load card back
    img = Image.open(f"assets/cardbacks/{file_tier}{sac}Cardback.png").convert("RGBA")
    image = costs.get_temple_variant(img, temple)
    image = image.resize((image.width * 10, image.height * 10), Image.NEAREST)

    # Load name
    name = csv_dict['Card Name']
    cost = costs.get_cost(csv_dict['Cost'] if csv_dict['Cost'].upper() not in ['NONE', '', 'FREE'] else None)

    if config["text_over_art"]:
        paste_card_art(name, image, cost, temple)

    # Determine the tribe list.
    tribes = csv_dict['Tribes'].split(' ') if csv_dict['Tribes'] not in ['None', ''] else []

    # Determine if a conduit indicator will need to be on the card because of the ''Conduit'' tribe.
    conduit = None
    conduit_img = None
    if "Conduit" in tribes and config["conduit_tribe_overlay"]:
        conduit = "NullConduit"

    # Generate sigil and trait list
    sigil_list, trait_list, has_attack_sigil, conduit = get_sigil_and_trait_list(csv_dict, conduit)

    # If a conduit indicator is needed, we try to fetch the right one. (Conduit sigils come with their own indicator)
    if conduit:
        conduit_img = Image.open(f"assets/conduit_indicators/{conduit}.png").convert("RGBA")

    # Write text
    draw_text(image, name, tier, temple, tribes, csv_dict["Flavor Text"])

    # Generate sigils and traits

    # This represents the starting height at which to draw the sigils.
    sigil_y = config['sigil_top_height']
    if conduit:
        sigil_y += conduit_img.height

    can_draw_sigils = config["allow_default_formatting"]
    if can_draw_sigils:
        # Try to use default format

        can_draw_sigils, image = draw_sigils(
            image, temple, tier, file_tier, sac, bloodless, conduit,
            conduit_img, sigil_y, sigil_list, trait_list,
            True
        )

    if not can_draw_sigils and config["allow_shorter_formatting"]:
        # Try to use shorter format

        can_draw_sigils, image = draw_sigils(
            image, temple, tier, file_tier, sac, bloodless, conduit,
            conduit_img, sigil_y, sigil_list, trait_list,
            False
        )

    if not can_draw_sigils and config["allow_base_game_display"]:
        # Use base game display

        image = draw_base_game_display(image, conduit, conduit_img, sigil_list)

    if not config["text_over_art"]:
        paste_card_art(name, image, cost, temple)

    # Print stats
    draw = ImageDraw.Draw(image)
    heavyweight_font = ImageFont.truetype(FONT, config['stats'])
    health = int(csv_dict['Health'] if csv_dict['Health'] not in ["x", "X", ''] else 0)
    draw.text(config['health_coord'], str(health), fill="black", font=heavyweight_font)
    if not (has_attack_sigil and
            (config["remove_power_stat_when_attack_sigil_present"] or config["attack_sigil_on_power_stat"])):
        power = int(csv_dict['Power'] if csv_dict['Power'] not in ["x", "X", ''] else 0)
        power_coord = config['power_coord'].get(temple if not bloodless else 'Terrain')
        draw.text(power_coord, str(power), fill="black", font=heavyweight_font)

    return image, name
