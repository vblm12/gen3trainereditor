#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Party:
    def add_mon(self, mon):
        self.mons.append(mon)

class Trainer:
    def get_ai_flags(self):
        flags = ''
        if self.check_bad_move:
            flags += 'AI_SCRIPT_CHECK_BAD_MOVE'
        if self.try_to_faint:
            flags += ' | AI_SCRIPT_TRY_TO_FAINT'
        if self.check_viability:
            flags += ' | AI_SCRIPT_CHECK_VIABILITY'
        if self.setup_first_turn:
            flags += ' | AI_SCRIPT_SETUP_FIRST_TURN'
        if self.risky:
            flags += ' | AI_SCRIPT_RISKY'
        if flags == '':
            flags += '0'
        return flags

class Mon:
    pass

def parse_party(lines):
    party = Party()
    party.party_type = lines[0].split()[3][len('TrainerMon'):]
    party.identifier = lines[0].split()[4].rstrip('[]')
    party.mons = []
    mon = Mon()
    for line in lines[2:]:
        tokens = line.split()
        if tokens[-1].rstrip(',') == '}':
            party.add_mon(mon)
            mon = Mon()
        elif tokens[0][0] == '.':
            if tokens[0] == '.moves':
                moves = []
                for move in tokens[2:]:
                    moves.append(move.rstrip(','))
                setattr(mon, 'moves', moves)
            else:
                setattr(mon, tokens[0].lstrip('.'), tokens[-1].rstrip(','))
    return party

def get_parties():
    parties = {}
    with open('src/data/trainer_parties.h') as f:
        party_lines = []
        for line in f:
            if line == '\n':
                continue
            elif line == "};\n":
                party = parse_party(party_lines)
                parties[party.identifier] = party
                party_lines = []
            else:
                party_lines.append(line.rstrip('\n'))
    return parties

def get_trainers():
    trainers = {}
    trainer = Trainer()
    with open('src/data/trainers.h') as f:
        for line in f:
            if line == '};\n':
                break
            tokens = line.split()
            if line == '\n' or tokens[0] == 'const' or tokens[0] == '{':
                continue
            elif tokens[0] == '},':
                trainers[trainer.identifier] = trainer
                trainer = Trainer()
            elif tokens[0][0] == '[':
                trainer.identifier = tokens[0].lstrip('[').rstrip(']')
            elif tokens[0] == '.partyFlags':
                party_flags = []
                for token in tokens[2:]:
                    if token == '|':
                        continue
                    party_flags.append(token.rstrip(','))
                trainer.party_flags = party_flags
            elif tokens[0] == '.trainerClass':
                trainer.trainer_class = tokens[-1].rstrip(',')
            elif tokens[0] == '.encounterMusic_gender':
                emg = []
                for token in tokens[2:]:
                    if token == '|':
                        continue
                    emg.append(token.rstrip(','))
                trainer.encounter_music_gender = emg
            elif tokens[0] == '.trainerPic':
                trainer.trainer_pic = tokens[-1].rstrip(',')
            elif tokens[0] == '.trainerName':
                trainer.name = line.split('"')[1]
            elif tokens[0] == '.items':
                if tokens[-1] == '{},':
                    trainer.items = []
                    continue
                else:
                    items = []
                    for token in tokens[2:]:
                        items.append(token.lstrip('{').rstrip('},'))
                    trainer.items = items
            elif tokens[0] == '.doubleBattle':
                if tokens[-1] == 'TRUE,':
                    trainer.double_battle = True
                else:
                    trainer.double_battle = False
            elif tokens[0] == '.aiFlags':
                ai_flags = []
                for token in tokens[2:]:
                    if token == '|':
                        continue
                    ai_flags.append(token.rstrip(','))
                trainer.check_bad_move = True if 'AI_SCRIPT_CHECK_BAD_MOVE' in ai_flags else False
                trainer.try_to_faint = True if 'AI_SCRIPT_TRY_TO_FAINT' in ai_flags else False
                trainer.check_viability = True if 'AI_SCRIPT_CHECK_VIABILITY' in ai_flags else False
                trainer.setup_first_turn = True if 'AI_SCRIPT_SETUP_FIRST_TURN' in ai_flags else False
                trainer.risky = True if 'AI_SCRIPT_RISKY' in ai_flags else False
            elif tokens[0] == '.party':
                trainer.party = tokens[-1].rstrip('},')
    return trainers

def flags_to_string(flags):
    if len(flags) == 1:
        return '{}'.format(flags[0])
    flags_str = ""
    for count, flag in enumerate(flags, start=1):
        if count == len(flags):
            flags_str += flag
        else:
            flags_str += "{} | ".format(flag)
    return flags_str

def write_opponents_header(trainers):
    with open('include/constants/opponents.h', 'w') as f:
        print('#ifndef GUARD_CONSTANTS_OPPONENTS_H', file=f)
        print('#define GUARD_CONSTANTS_OPPONENTS_H\n', file=f)
        for count, trainer in enumerate(trainers.values()):
            trainer_string = "#define {}".format(trainer.identifier)
            print("{} {:>{}}".format(trainer_string, count, 34-len(trainer_string)), file=f)
        print("\n#define TRAINERS_COUNT {0:>12}\n".format(len(trainers)), file=f)
        print("#endif  // GUARD_CONSTANTS_OPPONENTS_H", file=f)

def array_text_generator(items):
    string = ''
    for count, item in enumerate(items, start=1):
        if count == len(items):
            string += item
        else:
            string += item + ', '
    return string

def write_trainers_header(trainers, parties):
    with open('src/data/trainers.h', 'w') as f:
        print('const struct Trainer gTrainers[] = {', file=f)
        for count, trainer in enumerate(trainers.values(), start=1):
            print('    [{}] ='.format(trainer.identifier), file=f)
            print('    {', file=f)
            print('        .partyFlags = {},'.format(flags_to_string(trainer.party_flags)), file=f)
            print('        .trainerClass = {},'.format(trainer.trainer_class), file=f)
            print('        .encounterMusic_gender = {},'.format(flags_to_string(trainer.encounter_music_gender)), file=f)
            print('        .trainerPic = {},'.format(trainer.trainer_pic), file=f)
            print('        .trainerName = _("{}"),'.format(trainer.name), file=f)
            if not hasattr(trainer, 'items'):
                print('        .items = {{}},', file=f)
            else:
                print('        .items = {{{}}},'.format(array_text_generator(trainer.items)), file=f)
            print('        .doubleBattle = {},'.format("TRUE" if trainer.double_battle else "FALSE"), file=f)
            print('        .aiFlags = {},'.format(trainer.get_ai_flags()), file=f)
            print('        .partySize = {},'.format('0' if trainer.identifier == 'TRAINER_NONE' else 'ARRAY_COUNT({})'.format(trainer.party)), file=f)
            if trainer.identifier == 'TRAINER_NONE':
                print('        .party = {.NoItemDefaultMoves = NULL},', file=f)
            else:
                print('        .party = {{.{} = {}}},'.format(parties[trainer.party].party_type, trainer.party), file=f)
            print('    },', file=f)
            if count != len(trainers):
                print(file=f)
        print('};', file=f)

def write_parties_header(parties):
    with open('src/data/trainer_parties.h', 'w') as f:
        for count, party in enumerate(parties.values(), start=1):
            print('static const struct {} {}[] = {{'.format('TrainerMon{}'.format(party.party_type), party.identifier), file=f)
            for mon_count, mon in enumerate(party.mons, start=1):
                print('    {', file=f)
                print('    .iv = {},'.format(mon.iv), file=f)
                print('    .lvl = {},'.format(mon.lvl), file=f)
                print('    .species = {},'.format(mon.species), file=f)
                if hasattr(mon, 'heldItem'):
                    print('    .heldItem = {}{}'.format(mon.heldItem, ',' if hasattr(mon, 'moves') else ''), file=f)
                if hasattr(mon, 'moves'):
                    print('    .moves = {}'.format(array_text_generator(mon.moves)), file=f)
                if mon_count == len(party.mons):
                    print('    }', file=f)
                else:
                    print('    },', file=f)
            if count == len(parties):
                print('};', file=f)
            else:
                print('};\n', file=f)

@Gtk.Template.from_file('searchable_popover.ui')
class SearchablePopover(Gtk.Popover):
    __gtype_name__ = 'SearchablePopover'
    search_entry = Gtk.Template.Child()
    list_box = Gtk.Template.Child()
    grid = Gtk.Template.Child()
    search_string = ""

    def __init__(self, width = 200, height = 400):
        super().__init__()
        self.set_size_request(width, height)
        self.list_box.set_filter_func(self.filter_row)

    def add_item(self, label):
        label = Gtk.Label.new(label)
        self.list_box.insert(label, -1)
        label.show()

    @Gtk.Template.Callback('on_search')
    def on_search(self, entry):
        self.search_string = entry.get_text()
        self.list_box.invalidate_filter()

    def filter_row(self, row):
        return self.search_string.upper() in row.get_children()[0].get_text()


class Editor:
    items = {
        'ITEM_POTION': 'Potion',
        'ITEM_SUPER_POTION': 'Super Potion',
        'ITEM_HYPER_POTION': 'Hyper Potion',
        'ITEM_FULL_RESTORE': 'Full Restore'
    }
    def __init__(self):
        self.trainers = get_trainers()
        self.parties = get_parties()
        self.current_trainer = None
        builder = Gtk.Builder()
        builder.add_from_file('editor.ui')

        for widget in ['window', 'save_button', 'choose_trainer_button',
                       'choose_trainer_label', 'identifier_entry', 'class_button',
                       'class_label', 'music_button', 'music_label',
                       'sprite_button', 'sprite_label', 'double_battle_switch',
                       'check_bad_move_switch', 'check_viability_switch', 'setup_first_turn_switch',
                       'item_button1', 'item_label1', 'item_button2',
                       'item_label2', 'item_button3', 'item_label3',
                       'item_label4', 'item_button4', 'mon_button1',
                       'mon_label1', 'mon_button2', 'mon_label2',
                       'mon_button3', 'mon_label3', 'mon_button4',
                       'mon_label4', 'mon_button5', 'mon_label5',
                       'mon_button6', 'mon_label6', 'trainer_list_box',
                       'try_to_faint_switch', 'trainer_name_entry_main',
                       'risky_switch', 'item_popover', 'item_list_box']:
            setattr(self, widget, builder.get_object(widget))

        self.trainer_popover = SearchablePopover(300, 450)
        self.trainer_popover.list_box.connect('row-activated', self.on_trainer_row_activated)
        self.choose_trainer_button.set_popover(self.trainer_popover)
        self.trainer_popover.set_relative_to(self.choose_trainer_button)
        for trainer in self.trainers:
            if trainer == 'TRAINER_NONE':
                continue
            self.trainer_popover.add_item(trainer)

        for item in self.items:
            label = Gtk.Label.new(self.items[item])
            self.item_list_box.insert(label, -1)
            label.show()

        builder.connect_signals(self)

    def on_quit(self, data):
        Gtk.main_quit()

    def on_save(self, data):
        write_parties_header(self.parties)
        write_opponents_header(self.trainers)
        write_trainers_header(self.trainers, self.parties)

    def on_new_trainer_clicked(self, data):
        pass

    def on_item_button_toggled(self, button):
        if button.get_active():
            self.item_popover.set_relative_to(button)

    def on_switch_activate(self, switch, data):
        trainer = self.trainers[self.current_trainer]
        if switch == self.double_battle_switch:
            trainer.double_battle = switch.get_active()
        elif switch == self.check_bad_move_switch:
            trainer.double_battle = switch.get_active()
        elif switch == self.try_to_faint_switch:
            trainer.double_battle = switch.get_active()
        elif switch == self.check_viability_switch:
            trainer.double_battle = switch.get_active()
        elif switch == self.setup_first_turn_switch:
            trainer.double_battle = switch.get_active()
        elif switch == self.risky_switch:
            trainer.risky = self.risky_switch.get_state()

    def on_trainer_row_activated(self, box, row):
        self.current_trainer = row.get_children()[0].get_text()
        trainer = self.trainers[self.current_trainer]
        party = self.parties[trainer.party]
        self.trainer_name_entry_main.set_text(trainer.name)
        self.identifier_entry.set_text(trainer.identifier)
        self.class_label.set_text(trainer.trainer_class)
        #self.music_label.set_text(trainer.encounter_music_gender)
        self.sprite_label.set_text(trainer.trainer_pic)
        self.double_battle_switch.set_active(trainer.double_battle)

        self.check_bad_move_switch.set_active(trainer.check_bad_move)
        self.try_to_faint_switch.set_active(trainer.try_to_faint)
        self.check_viability_switch.set_active(trainer.check_viability)
        self.setup_first_turn_switch.set_active(trainer.setup_first_turn)

        if len(trainer.items) > 0:
            for count, item in enumerate(trainer.items, start=1):
                getattr(self, 'item_label{}'.format(count)).set_text('Select Item' if item == "ITEM_NONE" else item)
        else:
            for i in range(1,5):
                getattr(self, 'item_label{}'.format(i)).set_text('Select Item')

        for i in range(1,5):
            if i <= len(party.mons):
                getattr(self, 'mon_label{}'.format(i)).set_text(party.mons[i-1].species)
            else:
                getattr(self, 'mon_label{}'.format(i)).set_text('Select Pokemon')


if __name__ == "__main__":
    editor = Editor()
    Gtk.main()

