#%%
import subprocess
import watchdog.events
import watchdog.observers
import time
import json
from pathlib import Path
from utils.utils import *

#my_dir = Path(r'C:/Py/DS_Viz_Exp/data')
#ds_dir = Path(r"C:/Py/DS_Viz_Exp/viz/savefiles")

#* function to transform slot into json
def slot_to_json(slot_path):

    lenpt = len(slot_path)                          # len of whole path
    pt = slot_path[-1*(lenpt-89):]                   # just the file name, 89 filepath leng

    #print(pt)

    sv_path = r'C:/Users/e_par/AppData/LocalLow/Dry Cactus/Poly Bridge 2/SaveSlots/FourteenMeterOverpass/'

    #print(sv_path+pt)
    print('calling node...')
    p = subprocess.Popen(['C:/Program Files/nodejs/node', 'C:/Py/DS_Viz_Exp/scripts/polyparser.js', 'slot', f'{sv_path}{pt}'], stdout=subprocess.PIPE)
    out = p.stdout.read()
    print(out)

    pt_json = pt.replace('.slot', '.json')

    with open(f'{my_dir}/json/{pt_json}', 'w', encoding='utf-8') as f:
        json.dump(json.loads(str(out, 'utf-8')), f, ensure_ascii=False, indent=4)

    new_jsonp = f'{my_dir}/json/{pt_json}'

    return new_jsonp

#* get original dataset
#dataset = read_dataset(ds_dir, 'dataset_quant')

#%%
#! watchdog to check for new save files
class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        # Set the patterns for PatternMatchingEventHandler
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=['*.slot'],
                                                                ignore_directories=True, case_sensitive=False)

    def on_created(self, event):
        print("Watchdog received created event - % s." % event.src_path)

        # transform slot to json
        filep = slot_to_json(event.src_path)

        add_solution_to_dataset(dataset,filep,ds_dir)

        # Event is created, you can process it now

    #def on_modified(self, event):
    #        print("Watchdog received modified event - % s." % event.src_path)
    #        Event is modified, you can process it now

if __name__ == "__main__":
    src_path = r"C:/Users/e_par/AppData/LocalLow/Dry Cactus/Poly Bridge 2/SaveSlots/FourteenMeterOverpass"
    event_handler = Handler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path=src_path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()







#%%

#%%
'''
p = subprocess.Popen(['C:/Program Files/nodejs/node', 'polyparser.js', 'slot', 'C:/Users/e_par/Downloads/9ZDod.slot'], stdout=subprocess.PIPE)
out = p.stdout.read()
print(out)
# %%
'''