from PIL import Image
from model import config, logging

TEMPLES = config["temples"]


def get_temple_variant(image, temple):
    if temple not in TEMPLES:
        raise ValueError(f"'{temple}' is not a valid temple.")
    width, height = image.size
    version_height = height // len(TEMPLES)
    version_index = TEMPLES.index(temple)
    top = version_index * version_height
    bottom = (version_index + 1) * version_height
    return image.crop((0, top, width, bottom))


class Blood:

    def __init__(self, amount: int):
        self.amount = amount

    def __add__(self, other):
        if type(other) is not Blood:
            raise TypeError("Add operation can only be performed on two resources of the same type")
        return Blood(self.amount + other.amount)

    def __sub__(self, other):
        if type(other) is not Blood:
            raise TypeError("Sub operation can only be performed on two resources of the same type")
        return Blood(self.amount - other.amount)

    def getCostImage(self, temple: str) -> Image:
        img = Image.open(f"assets/costs/blood/blood.png").convert("RGBA")
        cost_img = get_temple_variant(img, temple)

        total_width = cost_img.width * self.amount
        final_img = Image.new('RGBA', (total_width, cost_img.height))
        for i in range(self.amount):
            x_offset = i * cost_img.width
            final_img.paste(cost_img, (x_offset, 0))

        return final_img


class Bones:

    def __init__(self, amount: int):
        self.amount = amount

    def __add__(self, other):
        if type(other) is not Bones:
            raise TypeError("Add operation can only be performed on two resources of the same type")
        return Bones(self.amount + other.amount)

    def __sub__(self, other):
        if type(other) is not Bones:
            raise TypeError("Sub operation can only be performed on two resources of the same type")
        return Bones(self.amount - other.amount)

    def getCostImage(self, temple: str) -> Image:
        if self.amount > 4:
            img = Image.open(f"assets/costs/bones/bones{self.amount}.png").convert("RGBA")
            return get_temple_variant(img, temple)

        img = Image.open("assets/costs/bones/bones.png").convert("RGBA")
        version_img = get_temple_variant(img, temple)

        duplicate_image = version_img.copy()
        final_width = version_img.width + (duplicate_image.width - 10) * (self.amount - 1)
        final_image = Image.new('RGBA', (final_width, version_img.height))
        final_image.paste(version_img, (0, 0))

        for i in range(self.amount - 1):
            paste_position = (version_img.width + (duplicate_image.width - 10) * i - 10, 0)
            final_image.paste(duplicate_image, paste_position, duplicate_image)

        return final_image


class Energy:

    def __init__(self, current_energy: int = 0, max_energy: int = 0):
        self.current_energy = current_energy
        self.max_energy = max_energy

    def __add__(self, other):
        if type(other) is not Energy:
            raise TypeError("Add operation can only be performed on two resources of the same type")
        return Energy(self.current_energy + other.current_energy, self.max_energy + other.max_energy)

    def __sub__(self, other):
        if type(other) is not Energy:
            raise TypeError("Sub operation can only be performed on two resources of the same type")
        return Energy(self.current_energy - other.current_energy, self.max_energy - other.max_energy)

    def getCostImage(self, temple: str) -> Image:
        if self.current_energy > 6:
            img = Image.open(f"assets/costs/energy/energy{self.current_energy}.png").convert("RGBA")
            energy_img = get_temple_variant(img, temple)
            if self.max_energy > 0:
                img = Image.open(f"assets/costs/energy/overcharge{self.max_energy}.png").convert("RGBA")
                overcharge_img = get_temple_variant(img, temple)
                cost_img = Image.new("RGBA", (energy_img.width + overcharge_img.width, energy_img.height))
                cost_img.paste(energy_img)
                cost_img.paste(overcharge_img, (energy_img.width, 0))
            else:
                cost_img = energy_img
        else:
            img = Image.open("assets/costs/energy/energy_bar.png").convert("RGBA")
            cost_img = get_temple_variant(img, temple)

            x_index = img.width - 10 * 4
            overcharge = Image.open("assets/costs/energy/overcharge.png").convert("RGBA")
            for _ in range(self.max_energy):
                cost_img.paste(overcharge, (x_index, 20))
                x_index -= 40
            energy = Image.open("assets/costs/energy/energy.png").convert("RGBA")
            for _ in range(self.current_energy - self.max_energy):
                cost_img.paste(energy, (x_index, 20))
                x_index -= 40
        return cost_img


class Gems:

    def __init__(self, *gems: str):
        self.gems = list(gems)

    def __add__(self, other):
        if type(other) not in [Gems, str]:
            raise TypeError('Add operation between gems may only be done with objects of type Gems or str.')
        self.gems += other.gems if type(other) is Gems else [other]

    def __sub__(self, other):
        if type(other) not in [Gems, str]:
            raise TypeError('Sub operation between gems may only be done with objects of type Gems or Gem.')
        if type(other) is str:
            other = [other]
        for gem in other:
            if gem in self.gems:
                self.gems.remove(gem)

    def copy(self):
        return Gems(*self.gems[:])

    @staticmethod
    def getGemImage(gem, temple) -> Image:
        shatter = "shattered_" if "shattered" in gem else ""
        gem = gem.split(" ")[-1].lower()
        color = dict(emeralds="emerald", sapphires="sapphire", rubies="ruby",
                     topazes="topaz", amethysts="amethyst", garnets="garnet", prisms="prism").get(gem, gem)
        img = Image.open(f"assets/costs/gems/{shatter}{color.lower()}.png").convert("RGBA")
        return get_temple_variant(img, temple)

    def getCostImage(self, temple: str) -> Image:
        gem_images = []
        for gem in self.gems:
            image = self.getGemImage(gem, temple)
            for _ in range(int(gem.split(" ")[0])):
                gem_images.append(image)

        total_width = sum(img.width for img in gem_images) - (len(gem_images) - 1) * 10
        max_height = max(img.height for img in gem_images)

        cost_image = Image.new("RGBA", (total_width, max_height), (255, 255, 255, 0))

        offset = 0
        for img in gem_images:
            if img.height == 90 and img.height != max_height:
                paste_position = (offset, 10)
            else:
                paste_position = (offset, 0)

            cost_image.paste(img, paste_position, mask=img)
            offset += img.width - 10
        return cost_image


class Distress:

    def __init__(self, amount: int):
        self.amount = amount

    def __add__(self, other):
        if type(other) is not Distress:
            raise TypeError("Add operation can only be performed on two resources of the same type")
        return Distress(self.amount + other.amount)

    def __sub__(self, other):
        if type(other) is not Distress:
            raise TypeError("Sub operation can only be performed on two resources of the same type")
        return Distress(self.amount - other.amount)

    def getCostImage(self, temple: str) -> Image:
        if self.amount > 6:
            img = Image.open(f"assets/costs/insanity/distress{self.amount}.png").convert("RGBA")
            return get_temple_variant(img, temple)

        img = Image.open("assets/costs/insanity/distress_bar.png").convert("RGBA")
        version_img = get_temple_variant(img, temple)

        if self.amount == 1:
            return version_img

        final_width = self.amount * (version_img.width - 30) + 30
        final_image = Image.new('RGBA', (final_width, version_img.height))

        x_pos = 0
        for i in range(self.amount):
            if i == 0:
                bar = version_img.copy().crop((0, 0, version_img.width - 20, version_img.height))
                final_image.paste(bar, (x_pos, 0))
            elif i == self.amount - 1:
                bar = version_img.copy().crop((10, 0, version_img.width, version_img.height))
                final_image.paste(bar, (x_pos, 0))
            else:
                bar = version_img.copy().crop((10, 0, version_img.width - 20, version_img.height))
                final_image.paste(bar, (x_pos, 0))
            x_pos += bar.width
        return final_image


def get_cost(strcost):
    cost = []
    if strcost is None:
        return cost
    try:
        for c in strcost.split(" + "):
            # Blood
            if "blood" in c:
                cost.append(Blood(int(c.split(" ")[0])))

            # Bones
            elif "bone" in c:
                cost.append(Bones(int(c.split(" ")[0])))

            # Energy
            elif "energy" in c or "max" in c:
                energy = None
                i = 0
                while energy is None and i < len(cost):
                    if isinstance(cost[i], Energy):
                        energy = cost[i]

                if "energy" in c:  # Current Energy
                    if energy:
                        energy.current_energy = int(c.split(" ")[0])
                    else:
                        cost.append(Energy(current_energy=int(c.split(" ")[0])))

                elif "max" in c:  # Maximum Energy
                    if energy:
                        energy.max_energy = int(c.split(" ")[0])
                    else:
                        cost.append(Energy(max_energy=int(c.split(" ")[0])))

            # Gems
            elif any(gem in c for gem in
                     ["emerald", "sapphire", "ruby", "rubies", "topaz", "amethyst", "garnet", "prism"]):
                gems = None
                i = 0
                while gems is None and i < len(cost):
                    if isinstance(cost[i], Gems):
                        gems = cost[i]
                    i += 1
                if gems:
                    gems += c
                else:
                    gems = Gems(c)
                    cost.append(gems)

            # Distress
            elif "distress" in c:
                cost.append(Distress(int(c.split(" ")[0])))

            # Add custom costs here with other elif
            else:
                raise KeyError(f"Unknown cost type: {c}")
        return cost
    except KeyError as e:
        print(f"Error: {e}")
        logging.error(f"Error: {e}")
