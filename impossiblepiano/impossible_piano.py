import discord
from redbot.core import commands
import random
from midiutil import MIDIFile

class ImpossiblePiano(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_random_note(self):
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octaves = [3, 4, 5, 6, 7]
        note = random.choice(notes)
        octave = random.choice(octaves)
        return f"{note}{octave}"

    def get_pitch(self, note):
        notes = {"C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65, "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71}
        octave = int(note[-1])
        note_name = note[:-1]
        pitch = notes[note_name] + (12 * (octave - 4))
        return pitch

    def generate_melody(self, length):
        melody = []
        for i in range(length):
            note = self.get_random_note()
            duration = random.uniform(0.1, 0.5)
            melody.append((note, duration))
        return melody

    def melody_to_midi(self, melody):
        midi = MIDIFile(1)
        midi.addTempo(0, 0, 120)
        track = 0
        channel = 0
        time = 0
        for note, duration in melody:
            pitch = self.get_pitch(note)
            velocity = 127
            midi.addNote(track, channel, pitch, time, duration, velocity)
            time += duration
        return midi

    @commands.command()
    async def piano(self, ctx):
        length = 20
        melody = self.generate_melody(length)
        midi_data = self.melody_to_midi(melody)
        with open("impossible_piano.mid", "wb") as output_file:
            midi_data.writeFile(output_file)

        voice_client = ctx.voice_client
        if not voice_client:
            if ctx.author.voice:
                voice_client = await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You must be in a voice channel to use this command.")
                return

        if voice_client.is_playing():
            voice_client.stop()

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("impossible_piano.mid"))
        voice_client.play(source)
        await ctx.send("Playing impossible piano song.")
