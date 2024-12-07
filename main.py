import os
import pathlib
import subprocess
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from fuzzywuzzy import process, fuzz

class Utils:
    @staticmethod
    def get_path(filename, from_home=False):
        base_dir = pathlib.Path.home() if from_home else pathlib.Path(
            __file__).parent.absolute()
        return os.path.join(base_dir, filename)

class PrimeNote:
    def __init__(self):
        self.notes_dir = os.path.join(str(pathlib.Path.home()), ".config", "primenote", "notes")
    
    def get_notes(self):
        notes = []
        if not os.path.exists(self.notes_dir):
            return notes
            
        for file in os.listdir(self.notes_dir):
            if file.endswith(".txt"):
                notes.append({
                    "filename": file,
                    "label": file[:-4],  # Remove .txt extension for display
                    "path": os.path.join(self.notes_dir, file)
                })
        return notes

    def open_note(self, note_data):
        subprocess.run(["pnote", "-n", "show", "-p", note_data["filename"]])

class PrimeNoteExtension(Extension):
    def __init__(self):
        super(PrimeNoteExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.primenote = PrimeNote()

    def get_search_results(self, query):
        query = query.lower() if query else ""
        notes = self.primenote.get_notes()
        items = []
        
        # Use fuzzy matching to find relevant notes
        matches = process.extract(
            query,
            choices=map(lambda n: n["label"], notes),
            limit=20,
            scorer=fuzz.partial_ratio
        )
        
        # Create result items for matches
        for match in matches:
            note = next((n for n in notes if n["label"] == match[0]), None)
            if note and match[1] > 80:  # Only show results with >80% match
                items.append(
                    ExtensionSmallResultItem(
                        icon=Utils.get_path("note.svg"),
                        name=note["label"],
                        on_enter=ExtensionCustomAction(note)
                    )
                )
        
        return items

class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        query = event.get_argument() or ""
        items = extension.get_search_results(query)
        return RenderResultListAction(items)

class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        note_data = event.get_data()
        extension.primenote.open_note(note_data)

class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        extension.keyword = event.preferences["pnote_kw"]

if __name__ == "__main__":
    PrimeNoteExtension().run()
