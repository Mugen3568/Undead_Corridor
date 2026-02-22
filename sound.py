import pygame as pg
from resource_helper import resource_path


class Sound:
    def __init__(self, game):
        self.game = game
        pg.mixer.init()
        self.path = resource_path('resources/sound/')
        
        # MUSIC: Louder (0.6)
        self.theme = pg.mixer.music.load(self.path + 'theme.mp3')
        pg.mixer.music.set_volume(0.6)
        
        # SFX: Quieter (0.3)
        self.player_pain = pg.mixer.Sound(self.path + 'player_pain.wav')
        self.player_pain.set_volume(0.3)
        
        # Enemy Sounds: Quieter
        self.npc_pain = pg.mixer.Sound(self.path + 'npc_pain.wav')
        self.npc_pain.set_volume(0.3)  # Fixes loud screaming
        
        self.npc_death = pg.mixer.Sound(self.path + 'npc_death.wav')
        self.npc_death.set_volume(0.3)
        
        self.npc_shot = pg.mixer.Sound(self.path + 'npc_attack.wav')
        self.npc_shot.set_volume(0.2)

        # --- WEAPON SOUNDS ---
        self.shotgun = pg.mixer.Sound(self.path + 'shotgun.wav')
        self.shotgun.set_volume(0.3)
        
        self.rifle = pg.mixer.Sound(self.path + 'rifle.mp3')
        self.rifle.set_volume(0.3)
        
        self.energy_cannon = pg.mixer.Sound(self.path + 'shotgun.wav')  # Placeholder SFX
        self.energy_cannon.set_volume(0.5)
        
        self.handgun = pg.mixer.Sound(self.path + 'pistol.mp3')
        self.handgun.set_volume(0.3)
        
        self.katana = pg.mixer.Sound(self.path + 'katana.mp3')
        self.katana.set_volume(0.3)

    def stop_weapons(self):
        # Stop specific weapon sounds to prevent "phantom" firing audio
        self.shotgun.stop()
        self.rifle.stop()
        self.handgun.stop()
        self.katana.stop()
        self.energy_cannon.stop()