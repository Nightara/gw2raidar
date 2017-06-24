from enum import IntEnum
from evtcparser import *
import pandas as pd
import numpy as np
from functools import reduce
from .collector import *
from .splits import *

class Skills:
    BLUE_PYLON_POWER = 31413
    BULLET_STORM = 31793
    UNSTABLE_MAGIC_SPIKE = 31392
    SPECTRAL_IMPACT = 31875
    GHASTLY_PRISON = 31623
    HEAVY_BOMB_EXPLODE = 31596
    TANTRUM = 34479
    BLEEDING = 736
    BURNING = 737
    VOLATILE_POISON = 34387
    UNBALANCED = 34367
    CORRUPTION = 34416

class BossMetricAnalyser:
    def __init__(self, agents, subgroups, players, bosses, phases):
        self.agents = agents
        self.subgroups = subgroups
        self.players = players
        self.bosses = bosses
        self.phases = phases
    
    def gather_boss_specific_stats(self, events, collector):
        if len(self.bosses[self.bosses.name == 'Vale Guardian']) != 0:
            self.gather_vg_stats(events, collector)
        elif len(self.bosses[self.bosses.name == 'Gorseval the Multifarious']) != 0:
            self.gather_gorse_stats(events, collector)
        elif len(self.bosses[self.bosses.name == 'Sabetha the Saboteur']) != 0:
            self.gather_sab_stats(events, collector)
        elif len(self.bosses[self.bosses.name == 'Slothasor']) != 0:
            self.gather_sloth_stats(events, collector)
        elif len(self.bosses[self.bosses.name == 'Matthias Gabrel']) != 0:
            self.gather_matt_stats(events, collector)
   
    def gather_vg_stats(self, events, collector):
        self.vg_blue_guardian_invul(events, collector)
        self.vg_bullets_eaten(events, collector)
        self.vg_teleports(events, collector)
        
    def vg_teleports(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_teleports(collector, events):
            collector.add_data('Teleports', len(events), int)
        
        relevent_events = events[(events.skillid == Skills.UNSTABLE_MAGIC_SPIKE) & events.dst_instid.isin(self.players.index) & (events.value > 0)]
        split_by_player_groups(subcollector, count_teleports, relevent_events, 'dst_instid', self.subgroups, self.players)
        
    def vg_bullets_eaten(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_bullets_eaten(collector, events):
            collector.add_data('Bullets Eaten', len(events), int)
        relevent_events = events[(events.skillid == Skills.BULLET_STORM) & events.dst_instid.isin(self.players.index) & (events.value > 0)]
        split_by_player_groups(subcollector, count_bullets_eaten, relevent_events, 'dst_instid', self.subgroups, self.players)

    def vg_blue_guardian_invul(self, events, collector):
        relevent_events = events[(events.skillid == Skills.BLUE_PYLON_POWER) & ((events.is_buffremove == 1) | (events.is_buffremove == 0))]
        time = 0
        start_time = 0
        buff_up = False
        for event in relevent_events.itertuples():
            if buff_up == False & (event.is_buffremove == 0):
                buff_up = True
                start_time = event.time
            elif buff_up == True & (event.is_buffremove == 1):
                buff_up = False
                time += event.time - start_time
        
        collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All").with_key(Group.SUBGROUP, "*All").add_data('Blue Guardian Invulnerability Time', time, int)
        
    def gather_gorse_stats(self, events, collector):
        self.gorse_spectral_impact(events, collector)
        self.gorse_ghastly_prison(events, collector)
        
    def gorse_spectral_impact(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics")
        def count_spectral_impacts_by_player_group(collector, events):
            def count_spectral_impacts(collector, events):
                collector.add_data('Unmitigated Spectral Impacts', len(events), int)
            split_by_player_groups(collector, count_spectral_impacts, events, 'dst_instid', self.subgroups, self.players)
        relevent_events = events[(events.skillid == Skills.SPECTRAL_IMPACT) & events.dst_instid.isin(self.players.index) & (events.value > 0)]
        split_by_phase(subcollector, count_spectral_impacts_by_player_group, relevent_events, self.phases)
        
    def gorse_ghastly_prison(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_ghastly_prison(collector, events):
            collector.add_data('Ghastly Imprisonments', len(events), int)
        
        relevent_events = events[(events.skillid == Skills.GHASTLY_PRISON) & events.dst_instid.isin(self.players.index) & (events.is_buffremove == 0)]
        split_by_player_groups(subcollector, count_ghastly_prison, relevent_events, 'dst_instid', self.subgroups, self.players)
        
    def gather_sab_stats(self, events, collector):
        self.sab_missed_bombs(events, collector)
        
    def sab_missed_bombs(self, events, collector):
        heavy_bomb_explosions = len(events[(events.skillid == Skills.HEAVY_BOMB_EXPLODE) & (events.is_buffremove == 1)])
        collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All").with_key(Group.SUBGROUP, "*All").add_data('Heavy Bombs Undefused', heavy_bomb_explosions, int)
        
    def gather_sloth_stats(self, events, collector):
        self.sloth_undodged_rocks(events, collector)
        self.sloth_spores_received(events, collector)
        self.sloth_spores_blocked(events, collector)
        self.sloth_volatile_poison(events, collector)
        
    def sloth_undodged_rocks(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_rocks(collector, events):
            collector.add_data('Tantrum Knockdowns', len(events), int)
        relevent_events = events[(events.skillid == Skills.TANTRUM) & events.dst_instid.isin(self.players.index) & (events.value > 0)]
        split_by_player_groups(subcollector, count_rocks, relevent_events, 'dst_instid', self.subgroups, self.players)
        
    def sloth_spores_received(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_spores_eaten(collector, events):
            collector.add_data('Spores Received', len(events) / 5, int)
        relevent_events = events[(events.skillid == Skills.BLEEDING) & events.dst_instid.isin(self.players.index) & (events.value > 0) & (events.is_buffremove == 0)]
        split_by_player_groups(subcollector, count_spores_eaten, relevent_events, 'dst_instid', self.subgroups, self.players)
        
    def sloth_spores_blocked(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_spores_eaten(collector, events):
            collector.add_data('Spores Blocked', len(events) / 5, int)
        relevent_events = events[(events.skillid == Skills.BLEEDING) & events.dst_instid.isin(self.players.index) & (events.value == 0) & (events.is_buffremove == 0)]
        split_by_player_groups(subcollector, count_spores_eaten, relevent_events, 'dst_instid', self.subgroups, self.players)
        
    def sloth_volatile_poison(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_volatile_poison(collector, events):
            collector.add_data('Volatile Poison Carrier', len(events), int)
        relevent_events = events[(events.skillid == Skills.VOLATILE_POISON) & events.dst_instid.isin(self.players.index) & (events.buff == 1) & (events.is_buffremove == 0)]
        split_by_player_groups(subcollector, count_volatile_poison, relevent_events, 'dst_instid', self.subgroups, self.players)
        
    def gather_matt_stats(self, events, collector):
        self.matt_unbalanced(events, collector)
        self.matt_burning_received(events, collector)
        self.matt_chosen_for_corruption(events, collector)
    
    def matt_unbalanced(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_unbalanced(collector, events):
            collector.add_data('Moved While Unbalanced', len(events), int)
        relevent_events = events[(events.skillid == Skills.UNBALANCED) & events.dst_instid.isin(self.players.index) & (events.buff == 0)]
        split_by_player_groups(subcollector, count_unbalanced, relevent_events, 'dst_instid', self.subgroups, self.players)
        
    def matt_burning_received(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics")
        def count_burning_received_by_player_group(collector, events):
            def count_burning_received(collector, events):
                collector.add_data('Burning Stacks Recieved', len(events), int)
            split_by_player_groups(collector, count_burning_received, events, 'dst_instid', self.subgroups, self.players)
        relevent_events = events[(events.skillid == Skills.BURNING) & events.dst_instid.isin(self.players.index) & events.src_instid.isin(self.bosses.index) & (events.value > 0) & (events.buff == 1) & (events.is_buffremove == 0)]
        split_by_phase(subcollector, count_burning_received_by_player_group, relevent_events, self.phases)
        
    def matt_chosen_for_corruption(self, events, collector):
        subcollector = collector.with_key(Group.CATEGORY, "combat").with_key(Group.METRICS, "mechanics").with_key(Group.PHASE, "All")
        def count_corrupted(collector, events):
            collector.add_data('Corrupted', len(events), int)
        relevent_events = events[(events.skillid == Skills.CORRUPTION) & events.dst_instid.isin(self.players.index) & (events.buff == 1) & (events.is_buffremove == 0)]
        split_by_player_groups(subcollector, count_corrupted, relevent_events, 'dst_instid', self.subgroups, self.players)