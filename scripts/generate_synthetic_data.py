"""
Synthetic Dataset Generator for SIH 2026 Civic Complaint Structuring & Classification AI.
Generates ~260 diverse, realistic civic complaints across 8 taxonomy categories.
Includes severity annotations, extracted signal ground truth, and Hinglish/Hindi variations.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "synthetic_reports.json"

# Base templates and realistic phrases for each category
SYNTHETIC_DATA_TEMPLATES = {
    "Water Supply": [
        ("Overhead water tank in Ward 4 has been overflowing continuously for 3 days. Clean drinking water flooding the road and entering houses.", "High", ["overflowing continuously", "3 days", "entering houses"]),
        ("Main water supply pipeline cracked near Morabadi ground. Water gushing out at high pressure for past 12 hours.", "High", ["pipeline cracked", "gushing out", "past 12 hours"]),
        ("No tap water supply in Sector 3 for the last 5 days. Handpumps are also dry. Residents are facing severe crisis.", "Critical", ["no tap water", "last 5 days", "severe crisis", "handpumps dry"]),
        ("Tap water coming from municipal supply is completely muddy and smells like sewage. Children falling sick with stomach ache.", "Critical", ["muddy water", "smells like sewage", "children falling sick"]),
        ("Community borewell motor burned out 2 days ago in Doranda. Over 40 families unable to get drinking water.", "High", ["motor burned out", "40 families", "unable to get drinking water"]),
        ("Sub-line water pipe leaking slowly on roadside near daily market. Clean water going into drain.", "Low", ["leaking slowly", "roadside"]),
        ("Water tanker did not arrive in our mohalla this morning. Kindly send the scheduled municipal tanker.", "Medium", ["tanker did not arrive", "scheduled"]),
        ("Paani ki pipeline toot gayi hai Chowk par, pichle 2 din se saara paani sadak par beh raha hai.", "High", ["pipeline toot gayi", "2 din", "paani sadak par beh raha"]),
        ("Overhead tank valve is loose causing water overflow every afternoon when pump turns on.", "Medium", ["valve loose", "overflow every afternoon"]),
        ("Drinking water pipeline contaminated with nearby drainage leakage. Dirty foul water in taps.", "Critical", ["contaminated", "drainage leakage", "dirty foul water"]),
        ("Public handpump handle broken near government primary school. Kids cannot drink water.", "Medium", ["handle broken", "primary school", "cannot drink water"]),
        ("Water supply pressure is extremely low on upper floors in Hindpiri area for past one week.", "Low", ["extremely low pressure", "past one week"]),
        ("Water tank sensor failed in municipal colony, tank overflowing non-stop since midnight.", "High", ["sensor failed", "overflowing non-stop", "since midnight"]),
        ("Drinking water pipeline laid 2 months ago has ruptured under road weight. Fresh water wasted.", "Medium", ["ruptured", "fresh water wasted"]),
        ("Severe water shortage in Ward 12. No supply for 4 days in this summer heat.", "Critical", ["severe water shortage", "no supply for 4 days", "summer heat"])
    ],
    "Electricity": [
        ("High-tension 11kV electrical wire snapped and hanging low right in front of primary school gate. Massive spark witnessed!", "Critical", ["11kV electrical wire snapped", "hanging low", "primary school", "massive spark"]),
        ("Distribution transformer sparking loudly and catching fire near Main Road market. Danger of blast!", "Critical", ["sparking loudly", "catching fire", "danger of blast"]),
        ("Unscheduled power outage in Bariatu for over 18 hours. Inverters drained, hospital patients struggling.", "High", ["outage over 18 hours", "hospital patients struggling"]),
        ("Wooden electric pole leaning dangerously at 45 degrees towards residential house after yesterday storm.", "High", ["leaning dangerously", "towards residential house"]),
        ("Street power junction box left open with live bare copper terminals exposed on pavement where children play.", "Critical", ["live bare terminals exposed", "children play"]),
        ("Frequent voltage fluctuation in Sector 4 damaging home refrigerators and appliances.", "Medium", ["frequent voltage fluctuation", "damaging appliances"]),
        ("Electric meter burnt with heavy smoke inside apartment staircase. Power cut off to building.", "High", ["meter burnt", "heavy smoke", "staircase"]),
        ("Street bijli ka wire toot kar sadak par gira hai, kabhi bhi current lag sakta hai kisi ko.", "Critical", ["wire toot kar sadak par gira", "current lag sakta hai"]),
        ("Phase failure in Colony B since morning. Single phase running, AC and water pumps not working.", "Medium", ["phase failure", "since morning", "pumps not working"]),
        ("Transformer oil leaking on the ground near tea stall. Loud humming noise coming continuously.", "Medium", ["oil leaking", "loud humming"]),
        ("Electric pole damaged after tractor collision. Wires entangled and touching tree branches.", "High", ["wires entangled", "touching tree branches"]),
        ("Power trip happening every 10 minutes in industrial area. Work completely disrupted.", "Medium", ["power trip every 10 minutes", "disrupted"]),
        ("Overhead cable sagged too low, getting entangled with passing trucks.", "High", ["overhead cable sagged", "entangled with trucks"]),
        ("Frequent power trippings in night time since last 3 days in Ward 7.", "Low", ["power trippings", "last 3 days"]),
        ("Transformer blown with loud blast, entire village in darkness since yesterday evening.", "High", ["blown with loud blast", "entire village in darkness"])
    ],
    "Roads & Infrastructure": [
        ("Huge 4-feet wide pothole on highway bridge bypass. Multiple two-wheelers slipping and falling daily.", "High", ["4-feet wide pothole", "two-wheelers slipping", "falling daily"]),
        ("Culvert collapsed after heavy rain on link road connecting village to town. Ambulance cannot pass!", "Critical", ["culvert collapsed", "ambulance cannot pass", "road cut off"]),
        ("Road digging done for gas pipeline left completely uncovered without barricades for 3 weeks.", "Medium", ["left uncovered without barricades", "3 weeks"]),
        ("Entire stretch of Main Street has craters and broken asphalt. Severe dust and back injuries to commuters.", "Medium", ["craters and broken asphalt", "back injuries"]),
        ("Waterlogging up to knee level on station road due to poor slope. Traffic halted for hours.", "High", ["waterlogging up to knee level", "traffic halted for hours"]),
        ("Sadak par bahut bada gaddha ho gaya hai, raat me bike wale gir rahe hain.", "High", ["bahut bada gaddha", "bike wale gir rahe hain"]),
        ("Speed breaker built without white markings or warning signs causing sudden brake accidents.", "Medium", ["speed breaker without markings", "accidents"]),
        ("Footpath tiles broken and open construction debris dumped on walking pathway.", "Low", ["footpath tiles broken", "debris dumped"]),
        ("Bridge expansion joint separated with 6-inch gap, vehicles experiencing severe tire shocks.", "High", ["expansion joint separated", "severe tire shocks"]),
        ("Freshly tarred road started peeling off within 2 days after first shower. Substandard work.", "Low", ["peeling off within 2 days", "substandard work"]),
        ("Large sinkhole formed in middle of busy intersection near bus stand.", "Critical", ["large sinkhole", "busy intersection"]),
        ("Dividers broken and iron rebar sticking out into road lane.", "High", ["iron rebar sticking out", "into road lane"]),
        ("Mud and gravel spread across curvy road causing bikes to skid.", "Medium", ["mud and gravel", "bikes to skid"]),
        ("Unfinished flyover ramp barricade knocked down, risk of vehicles driving into gap.", "Critical", ["risk of vehicles driving into gap"]),
        ("Minor potholes near colony entrance need patch repair before monsoon.", "Low", ["minor potholes", "patch repair"])
    ],
    "Sanitation & Waste": [
        ("Massive illegal garbage dump accumulating opposite government hospital. Rotting food and medical waste stinking horribly.", "Critical", ["opposite hospital", "medical waste", "rotting food"]),
        ("Open sewage drain blocked and overflowing black contaminated sludge onto residential walkway.", "High", ["overflowing black sludge", "residential walkway"]),
        ("Municipal koodadan overflowing for past 10 days. Stray cattle and dogs scattering plastic bags.", "Medium", ["overflowing for past 10 days", "dogs scattering waste"]),
        ("Commercial market meat waste and chicken remains dumped directly into open nallah, foul unbearable odor.", "High", ["meat waste dumped in nallah", "unbearable odor"]),
        ("Drain cover broken, sewage water backing up into ground floor houses during rain.", "High", ["sewage backing up into houses"]),
        ("Kachra gaadi has not visited Ward 9 for the last 6 days. Household garbage piled outside gates.", "Medium", ["kachra gaadi not visited", "last 6 days"]),
        ("Septic tank overflow running into street gutter and creating foul stench across neighborhood.", "High", ["septic tank overflow", "foul stench"]),
        ("Clogged storm drain full of plastic bottles and silt. Water stagnant for weeks.", "Medium", ["clogged storm drain", "stagnant for weeks"]),
        ("Gali ki naali jam ho gayi hai, ganda paani ghar ke samne jama hai.", "Medium", ["naali jam", "ganda paani jama hai"]),
        ("Open dumping yard burning plastic waste at night causing toxic smoke and breathing difficulty.", "Critical", ["burning plastic waste", "toxic smoke", "breathing difficulty"]),
        ("Public community toilet in slum area blocked with no running water for cleaning.", "High", ["toilet blocked", "no running water"]),
        ("Small pile of dry leaves and garden waste dumped on corner lot.", "Low", ["small pile", "dry leaves"]),
        ("Bio-waste dumped behind nursing home without proper incineration.", "Critical", ["bio-waste dumped", "behind nursing home"]),
        ("Dustbin wheels broken and tipped over, garbage lying on road.", "Low", ["dustbin broken", "lying on road"]),
        ("Construction silt dumped into municipal drainage canal causing blockage.", "Medium", ["silt dumped into drainage canal"])
    ],
    "Public Health": [
        ("Stagnant green water pool in abandoned plot breeding swarm of mosquitoes. 12 confirmed dengue cases in colony.", "Critical", ["swarm of mosquitoes", "12 confirmed dengue cases"]),
        ("Primary Health Center (PHC) locked during working hours, no doctor or basic anti-venom available.", "Critical", ["locked during working hours", "no doctor", "no anti-venom"]),
        ("Cow carcass lying on roadside near vegetable mandi for 2 days, flies everywhere, health hazard.", "High", ["carcass lying for 2 days", "flies everywhere", "health hazard"]),
        ("Children showing symptoms of skin infection and rashes after using municipal park with untreated standing water.", "High", ["children skin infection", "untreated standing water"]),
        ("No fogging or mosquito larvicide spraying done despite monsoon outbreak in Ward 15.", "Medium", ["no fogging done", "monsoon outbreak"]),
        ("Swasthya kendra me dawa bilkul khatam hai, bukhar ke mareez laut rahe hain.", "High", ["dawa khatam", "swasthya kendra", "mareez laut rahe"]),
        ("Dog bite victim went to government dispensary, anti-rabies injection out of stock.", "Critical", ["anti-rabies out of stock", "dog bite victim"]),
        ("Chemical fumes coming from illegal battery workshop next to residential houses, stinging eyes.", "High", ["chemical fumes", "stinging eyes", "illegal workshop"]),
        ("Dead pigs in drain creating severe bacterial contamination risk.", "High", ["dead pigs in drain", "contamination risk"]),
        ("Stagnant water near school canteen ground attracting flies and mosquitoes.", "Medium", ["stagnant water near school", "attracting flies"]),
        ("Suspected cholera cases reported after drinking contaminated well water.", "Critical", ["suspected cholera", "contaminated well water"]),
        ("Lack of hand sanitizer and hygiene supplies in rural health sub-center.", "Low", ["lack of hygiene supplies"]),
        ("Open defecation area near water source spreading gastrointestinal diseases.", "High", ["open defecation", "spreading gastrointestinal diseases"]),
        ("Foul chemical runoff from small dyeing unit entering soil.", "Medium", ["chemical runoff", "entering soil"]),
        ("Municipal clinic lacks emergency thermometer and BP apparatus.", "Low", ["lacks thermometer and BP apparatus"])
    ],
    "Education Infrastructure": [
        ("Government Primary School classroom roof slab cracked and chunks of concrete falling onto student desks!", "Critical", ["roof slab cracked", "concrete falling", "student desks"]),
        ("Boundary wall of girls high school collapsed, allowing stray animals and unauthorized intruders inside.", "High", ["boundary wall collapsed", "girls high school", "unauthorized intruders"]),
        ("School toilet for girl students has no running water, broken doors, and no latch. Girls forced to go home.", "High", ["school toilet no water", "broken doors", "girls forced to go home"]),
        ("Rainwater leaking through classroom ceiling onto books and electrical switchboard during class hours.", "High", ["rainwater leaking through ceiling", "switchboard during class"]),
        ("Primary school has no functional drinking water filter. Students drinking untreated borewell water.", "High", ["no functional drinking water filter", "untreated water"]),
        ("School building plaster peeling off and window glass broken in 3 classrooms.", "Medium", ["plaster peeling off", "window glass broken"]),
        ("School me bachhon ke baithne ke liye bench desk toota hua hai, zameen par baithna pad raha hai.", "Medium", ["bench desk toota", "zameen par baithna pad raha"]),
        ("Midday meal kitchen shed has asbestos roof broken with soot accumulation.", "Medium", ["kitchen shed broken", "soot accumulation"]),
        ("Kindergarten anganwadi center has damp walls with fungal mold all over.", "Medium", ["damp walls", "fungal mold"]),
        ("School playground inundated with 1 foot mud and dangerous iron scraps.", "Medium", ["inundated with mud", "dangerous iron scraps"]),
        ("School boundary fence missing allowing highway traffic right next to playground.", "High", ["boundary fence missing", "highway traffic next to playground"]),
        ("Blackboards faded and unreadable in all primary classes.", "Low", ["blackboards faded"]),
        ("Classroom ceiling fan hanging loosely by single wire over children.", "Critical", ["fan hanging loosely by single wire", "over children"]),
        ("School library room floor tiles cracked and uneven.", "Low", ["floor tiles cracked"]),
        ("No electricity in government secondary school during summer exam week.", "High", ["no electricity", "summer exam week"])
    ],
    "Public Safety": [
        ("All 14 streetlights on bypass road dead for 3 weeks. Complete pitch darkness leading to snatching and accidents.", "High", ["14 streetlights dead", "3 weeks", "pitch darkness", "snatching"]),
        ("Deep open uncovered storm manhole on unlit pedestrian footpath. Lethal death trap for pedestrians at night!", "Critical", ["open uncovered manhole", "unlit footpath", "lethal death trap"]),
        ("Pack of 8 aggressive stray dogs attacking cyclists and school children every evening near park.", "High", ["aggressive stray dogs", "attacking cyclists", "school children"]),
        ("Dark deserted alley under railway overbridge being used for illicit drug activities and harassment of women.", "High", ["illicit drug activities", "harassment of women", "dark alley"]),
        ("Manhole cover stolen on main market crossing, people putting tree branches as makeshift warning.", "High", ["manhole cover stolen", "tree branches as makeshift warning"]),
        ("Roadside tree trunk completely rotten and swinging in wind, could crush passing cars at any moment.", "Critical", ["tree trunk rotten", "could crush passing cars"]),
        ("Street light ka pole kharab hai, pichle ek mahine se andhera rehta hai colony me.", "Medium", ["pole kharab", "ek mahine se andhera"]),
        ("Unlit sharp curve on valley road missing warning reflectors and guard rails.", "High", ["missing warning reflectors", "guard rails", "sharp curve"]),
        ("Biting stray dogs around bus stop creating panic among morning walkers.", "Medium", ["biting stray dogs", "panic among walkers"]),
        ("Footpath railing missing over 20-foot drop into river canal.", "Critical", ["railing missing", "20-foot drop"]),
        ("Streetlight bulb blinking intermittently near house number 45.", "Low", ["bulb blinking intermittently"]),
        ("Damaged high security gate of municipal park left open at night.", "Low", ["security gate left open"]),
        ("Broken glass bottles deliberately smashed across children playground slide area.", "High", ["broken glass bottles", "children playground"]),
        ("Construction company left deep 10-foot trench without lighting or reflective tape on roadside.", "Critical", ["10-foot trench", "without lighting or reflective tape"]),
        ("Single street light faulty on dead-end residential lane.", "Low", ["single street light faulty"])
    ],
    "Other": [
        ("Illegal commercial loudspeaker blaring religious / party songs past midnight in silence zone near hospital.", "Medium", ["loudspeaker past midnight", "silence zone near hospital"]),
        ("Encroachment of public footpath by unauthorized vendor permanent tin sheds.", "Medium", ["encroachment of public footpath", "unauthorized tin sheds"]),
        ("Huge illegal political advertising hoarding blocking traffic signal visibility at main square.", "Medium", ["illegal hoarding", "blocking traffic signal"]),
        ("Municipal birth certificate counter clerk refusing to process applications without bribe.", "High", ["refusing to process applications", "administrative"]),
        ("Commercial diesel generator running continuously on pavement releasing thick black smoke.", "Medium", ["generator on pavement", "thick black smoke"]),
        ("Illegal parking of commercial tourist buses blocking colony main entrance gate.", "Low", ["illegal parking", "blocking colony entrance"]),
        ("Loud industrial machinery operating in residential basement without license.", "Medium", ["industrial machinery in residential basement", "without license"]),
        ("Park public benches damaged by miscreants.", "Low", ["benches damaged"]),
        ("Street name board twisted and unreadable.", "Low", ["street name board twisted"]),
        ("Illegal sand mining trucks driving through village small street at night.", "High", ["illegal sand mining trucks", "at night"]),
        ("Stray cattle blocking colony internal road.", "Low", ["stray cattle blocking"]),
        ("Request to prune overgrown tree branches touching private balcony.", "Low", ["overgrown tree branches"]),
        ("Abandoned rusted car chassis parked on street for 6 months taking up space.", "Low", ["abandoned rusted car", "6 months"]),
        ("Public notice board glass smashed.", "Low", ["notice board smashed"]),
        ("Municipal office delayed issuance of trade license for 4 months.", "Low", ["delayed issuance", "4 months"])
    ]
}

LOCATIONS = [
    "Ward 4, Near Water Tank, Morabadi, Ranchi (23.3850, 85.3340)",
    "Main Road, Near Overbridge, Kadru, Ranchi (23.3629, 85.3211)",
    "Sector 4/F, Bokaro Steel City (23.6693, 86.1511)",
    "Bank More, Near Shramik Chowk, Dhanbad (23.7957, 86.4304)",
    "Sakchi Bazaar, Near Post Office, Jamshedpur (22.8046, 86.2029)",
    "Bariatu Road, Opposite RIMS Gate, Ranchi (23.3980, 85.3580)",
    "Hazaribagh Town, Near Lake Road (23.9930, 85.3620)",
    "Deoghar Town, Near Tower Chowk (24.4826, 86.6976)",
    "Giridih, Near Pachamba Road (24.1850, 86.3050)",
    "Doranda, Near High Court Old Campus, Ranchi (23.3420, 85.3280)"
]

MODIFIERS = [
    (" Urgent attention needed immediately!", "High"),
    (" Please look into this at the earliest as public is suffering.", "Medium"),
    (" Multiple complaints registered earlier with ward councillor but no action taken.", "Medium"),
    (" Situation is deteriorating rapidly since this morning.", "High"),
    (" Small issue, kindly repair whenever staff is available in this sector.", "Low")
]


def generate_dataset(num_samples: int = 260) -> list:
    random.seed(42)
    records = []
    rec_id = 1

    # First, guarantee all explicit templates are present
    for category, items in SYNTHETIC_DATA_TEMPLATES.items():
        for text, severity, signals in items:
            loc = random.choice(LOCATIONS)
            records.append({
                "report_id": f"SYNTH_{rec_id:04d}",
                "text": text,
                "category": category,
                "severity": severity,
                "signals": signals,
                "location": loc,
                "is_synthetic": True,
                "dataset_split": "train" if (rec_id % 5 != 0) else "test"
            })
            rec_id += 1

    # Now augment to reach ~260 records
    categories = list(SYNTHETIC_DATA_TEMPLATES.keys())
    while len(records) < num_samples:
        cat = random.choice(categories)
        base_text, base_sev, base_signals = random.choice(SYNTHETIC_DATA_TEMPLATES[cat])
        mod_text, mod_sev = random.choice(MODIFIERS)

        # Create augmented text
        augmented_text = f"{base_text} {mod_text}".strip()
        final_sev = base_sev
        if mod_sev == "High" and base_sev in ["Medium", "High"]:
            final_sev = "High"
        elif mod_sev == "High" and base_sev == "Critical":
            final_sev = "Critical"

        signals = list(base_signals)
        loc = random.choice(LOCATIONS)

        records.append({
            "report_id": f"SYNTH_{rec_id:04d}",
            "text": augmented_text,
            "category": cat,
            "severity": final_sev,
            "signals": signals,
            "location": loc,
            "is_synthetic": True,
            "dataset_split": "train" if (rec_id % 5 != 0) else "test"
        })
        rec_id += 1

    return records


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records = generate_dataset(260)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully generated {len(records)} synthetic complaints at: {OUTPUT_FILE}")
    
    # Print summary statistics
    cat_counts = {}
    sev_counts = {}
    for r in records:
        cat_counts[r["category"]] = cat_counts.get(r["category"], 0) + 1
        sev_counts[r["severity"]] = sev_counts.get(r["severity"], 0) + 1
    
    print("\nCategory Distribution:")
    for k, v in sorted(cat_counts.items()):
        print(f"  - {k}: {v}")
    
    print("\nSeverity Distribution:")
    for k, v in sorted(sev_counts.items()):
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    main()
