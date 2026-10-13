"""
thali_library.py
Indian Food Composition Library based on ICMR - National Institute of Nutrition (NIN)
Indian Food Composition Tables (IFCT 2017) and published South Asian Glycemic Index tables.

Used by ThaliTwin for:
1. Translating cultural Indian meals into physiological macronutrient vectors (Carbs, Protein, Fat, Fiber).
2. Calculating meal Glycemic Load (GL) = (Net Carbs * GI) / 100.
3. Enabling clinical 'What-If' meal swap simulations and lifestyle counterfactuals.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(frozen=True)
class Dish:
    dish_id: str
    name: str
    regional_origin: str
    category: str  # Breakfast, Lunch/Dinner, Snack
    serving_description: str
    serving_weight_g: float
    calories_kcal: float
    carbs_g: float
    protein_g: float
    fat_g: float
    fiber_g: float
    glycemic_index: float
    glycemic_load: float
    typical_swap_target: Optional[str] = None
    clinical_notes: str = ""

# 25 Authentic Indian dishes across North, South, East, West & Pan-India
INDIAN_THALI_REGISTRY: Dict[str, Dish] = {
    "D01": Dish(
        dish_id="D01",
        name="Idli (2 pcs) with Sambar & Coconut Chutney",
        regional_origin="South India",
        category="Breakfast",
        serving_description="2 idlis (150g) + 100ml sambar + 2 tbsp chutney",
        serving_weight_g=280.0,
        calories_kcal=265.0,
        carbs_g=42.0,
        protein_g=7.5,
        fat_g=6.8,
        fiber_g=4.6,
        glycemic_index=68.0,
        glycemic_load=28.6,
        typical_swap_target="D09",
        clinical_notes="Fermented rice-dal batter. Moderate GI; sambar dal lowers peak slope slightly."
    ),
    "D02": Dish(
        dish_id="D02",
        name="Masala Dosa with Potato Masala & Chutney",
        regional_origin="South India",
        category="Breakfast",
        serving_description="1 large crisp dosa with 80g potato filling + chutney",
        serving_weight_g=220.0,
        calories_kcal=385.0,
        carbs_g=52.5,
        protein_g=6.2,
        fat_g=16.5,
        fiber_g=3.8,
        glycemic_index=76.0,
        glycemic_load=39.9,
        typical_swap_target="D09",
        clinical_notes="High glycemic index due to refined parboiled rice and mashed potato filling."
    ),
    "D03": Dish(
        dish_id="D03",
        name="Ven Pongal with Ghee & Pepper",
        regional_origin="South India (Tamil Nadu)",
        category="Breakfast",
        serving_description="1 medium bowl (180g)",
        serving_weight_g=180.0,
        calories_kcal=340.0,
        carbs_g=46.0,
        protein_g=7.8,
        fat_g=14.0,
        fiber_g=3.2,
        glycemic_index=72.0,
        glycemic_load=33.1,
        typical_swap_target="D04",
        clinical_notes="Rice-moong dal mash with ghee. High starch availability causes sustained peak."
    ),
    "D04": Dish(
        dish_id="D04",
        name="Ragi Mudde with Bassaru / Sambar",
        regional_origin="South India (Karnataka)",
        category="Lunch/Dinner",
        serving_description="1 ragi ball (200g) + 120ml leafy greens lentil curry",
        serving_weight_g=320.0,
        calories_kcal=295.0,
        carbs_g=45.0,
        protein_g=8.4,
        fat_g=2.8,
        fiber_g=9.6,
        glycemic_index=54.0,
        glycemic_load=24.3,
        typical_swap_target=None,
        clinical_notes="Finger millet staple with high dietary fiber and polyphenol content, attenuating glucose rise."
    ),
    "D05": Dish(
        dish_id="D05",
        name="Dal Tadka with Steamed Basmati Rice",
        regional_origin="Pan-India / North",
        category="Lunch/Dinner",
        serving_description="150g cooked white basmati rice + 150ml yellow toor dal",
        serving_weight_g=300.0,
        calories_kcal=410.0,
        carbs_g=64.0,
        protein_g=12.2,
        fat_g=8.5,
        fiber_g=5.2,
        glycemic_index=71.0,
        glycemic_load=45.4,
        typical_swap_target="D06",
        clinical_notes="Most common daily lunch across urban India. Substantial glycemic load if rice exceeds 1 cup."
    ),
    "D06": Dish(
        dish_id="D06",
        name="2 Phulka Rotis (Whole Wheat) with Bhindi Sabzi & Dal",
        regional_origin="North / West India",
        category="Lunch/Dinner",
        serving_description="2 medium rotis (80g) + 120g okra sabzi + 100ml dal",
        serving_weight_g=300.0,
        calories_kcal=330.0,
        carbs_g=44.0,
        protein_g=10.5,
        fat_g=7.5,
        fiber_g=8.4,
        glycemic_index=55.0,
        glycemic_load=24.2,
        typical_swap_target=None,
        clinical_notes="Optimal everyday meal. Whole wheat fiber + okra mucilage slows gastric emptying."
    ),
    "D07": Dish(
        dish_id="D07",
        name="Paneer Butter Masala with 1 Garlic Naan",
        regional_origin="North India",
        category="Lunch/Dinner",
        serving_description="180g paneer curry + 1 maida naan (90g)",
        serving_weight_g=270.0,
        calories_kcal=590.0,
        carbs_g=54.0,
        protein_g=18.5,
        fat_g=32.0,
        fiber_g=3.1,
        glycemic_index=74.0,
        glycemic_load=40.0,
        typical_swap_target="D06",
        clinical_notes="Refined flour (maida) combined with high saturated fat causes a biphasic, late-delayed glucose spike (Pizza effect)."
    ),
    "D08": Dish(
        dish_id="D08",
        name="Chicken / Vegetable Dum Biryani with Raita",
        regional_origin="Hyderabad / Pan-India",
        category="Lunch/Dinner",
        serving_description="280g spiced basmati rice & chicken/veggies + 80g curd raita",
        serving_weight_g=360.0,
        calories_kcal=540.0,
        carbs_g=62.0,
        protein_g=22.0,
        fat_g=21.0,
        fiber_g=4.2,
        glycemic_index=69.0,
        glycemic_load=42.8,
        typical_swap_target="D12",
        clinical_notes="Popular weekend feast; raita curd provides lactic acid slightly buffering digestion."
    ),
    "D09": Dish(
        dish_id="D09",
        name="Besan Chilla (2 pcs) with Mint & Coriander Chutney",
        regional_origin="North / West India",
        category="Breakfast",
        serving_description="2 gram-flour crepes (150g) with onions, tomatoes + chutney",
        serving_weight_g=180.0,
        calories_kcal=255.0,
        carbs_g=26.0,
        protein_g=13.5,
        fat_g=8.2,
        fiber_g=7.1,
        glycemic_index=38.0,
        glycemic_load=9.9,
        typical_swap_target=None,
        clinical_notes="Gram flour (chana dal flour) has low GI and high protein, ideal for morning postprandial stability."
    ),
    "D10": Dish(
        dish_id="D10",
        name="Poha with Peanuts, Curry Leaves & Peas",
        regional_origin="West / Central (Maharashtra/MP)",
        category="Breakfast",
        serving_description="1 medium plate flattened rice (180g)",
        serving_weight_g=180.0,
        calories_kcal=310.0,
        carbs_g=46.0,
        protein_g=6.8,
        fat_g=9.5,
        fiber_g=4.2,
        glycemic_index=66.0,
        glycemic_load=30.4,
        typical_swap_target="D09",
        clinical_notes="Flattened parboiled rice; quick enzymatic hydrolysis produces sharp 45-min peak."
    ),
    "D11": Dish(
        dish_id="D11",
        name="Vegetable Upma with Roasted Semolina",
        regional_origin="South / West India",
        category="Breakfast",
        serving_description="1 medium bowl (180g)",
        serving_weight_g=180.0,
        calories_kcal=275.0,
        carbs_g=42.0,
        protein_g=6.2,
        fat_g=8.0,
        fiber_g=3.8,
        glycemic_index=67.0,
        glycemic_load=28.1,
        typical_swap_target="D09",
        clinical_notes="Semolina (rava) base. Rapid starch absorption without added fiber or pulses."
    ),
    "D12": Dish(
        dish_id="D12",
        name="Rajma Masala with Brown Rice & Cucumber Salad",
        regional_origin="North India (Punjab)",
        category="Lunch/Dinner",
        serving_description="150g brown rice + 150g kidney bean curry + 60g salad",
        serving_weight_g=360.0,
        calories_kcal=390.0,
        carbs_g=54.0,
        protein_g=15.5,
        fat_g=6.2,
        fiber_g=11.2,
        glycemic_index=48.0,
        glycemic_load=25.9,
        typical_swap_target=None,
        clinical_notes="Outstanding resistant starch profile from kidney beans + brown rice fiber."
    ),
    "D13": Dish(
        dish_id="D13",
        name="Moong Dal Khichdi with 1 tsp Ghee & Curd",
        regional_origin="Pan-India",
        category="Lunch/Dinner",
        serving_description="220g khichdi + 100g plain homemade curd",
        serving_weight_g=320.0,
        calories_kcal=360.0,
        carbs_g=48.0,
        protein_g=12.8,
        fat_g=9.5,
        fiber_g=5.5,
        glycemic_index=58.0,
        glycemic_load=27.8,
        typical_swap_target=None,
        clinical_notes="Split yellow moong dal provides accessible amino acids; gentle digestion profile."
    ),
    "D14": Dish(
        dish_id="D14",
        name="Fish Curry (Mustard/Macher Jhol) with Steamed Rice",
        regional_origin="East India (Bengal) / Coastal",
        category="Lunch/Dinner",
        serving_description="150g rice + 120g rohu fish in light cumin-turmeric broth",
        serving_weight_g=300.0,
        calories_kcal=375.0,
        carbs_g=48.0,
        protein_g=24.0,
        fat_g=8.0,
        fiber_g=1.8,
        glycemic_index=64.0,
        glycemic_load=30.7,
        typical_swap_target=None,
        clinical_notes="High lean marine protein triggers early GLP-1 release, mitigating white rice spike."
    ),
    "D15": Dish(
        dish_id="D15",
        name="Masala Chai (with 1.5 tsp sugar) + 3 Marie Biscuits",
        regional_origin="Pan-India",
        category="Snack",
        serving_description="150ml tea + 3 biscuits (30g)",
        serving_weight_g=180.0,
        calories_kcal=195.0,
        carbs_g=32.0,
        protein_g=3.8,
        fat_g=4.8,
        fiber_g=0.8,
        glycemic_index=72.0,
        glycemic_load=23.0,
        typical_swap_target="D16",
        clinical_notes="Ubiquitous 4 PM corporate/household habit in India. Rapid sucrose spike with zero fiber barrier."
    ),
    "D16": Dish(
        dish_id="D16",
        name="Roasted Makhana (Foxnuts) with Unsweetened Green Tea",
        regional_origin="Pan-India / Bihar",
        category="Snack",
        serving_description="35g dry-roasted makhana with pinch of rock salt + green tea",
        serving_weight_g=40.0,
        calories_kcal=125.0,
        carbs_g=18.0,
        protein_g=4.2,
        fat_g=1.5,
        fiber_g=3.2,
        glycemic_index=42.0,
        glycemic_load=7.6,
        typical_swap_target=None,
        clinical_notes="Healthy replacement for evening biscuit habit. Low glycemic impact."
    ),
    "D17": Dish(
        dish_id="D17",
        name="Chole Bhature (1 Bhatura + Chickpea Curry)",
        regional_origin="North India (Delhi/Punjab)",
        category="Lunch/Dinner",
        serving_description="1 deep-fried bhatura (100g) + 180g spicy chickpea curry",
        serving_weight_g=280.0,
        calories_kcal=620.0,
        carbs_g=68.0,
        protein_g=14.5,
        fat_g=31.0,
        fiber_g=8.5,
        glycemic_index=72.0,
        glycemic_load=48.9,
        typical_swap_target="D12",
        clinical_notes="Deep-fried maida creates persistent glycemic excursion lasting 4+ hours."
    ),
    "D18": Dish(
        dish_id="D18",
        name="Sambar Sadam (Sambar Rice) with Appalam",
        regional_origin="South India",
        category="Lunch/Dinner",
        serving_description="250g sambar rice + 1 roasted papad",
        serving_weight_g=265.0,
        calories_kcal=380.0,
        carbs_g=58.0,
        protein_g=9.5,
        fat_g=9.0,
        fiber_g=5.8,
        glycemic_index=68.0,
        glycemic_load=39.4,
        typical_swap_target="D04",
        clinical_notes="Convenience lunch. Moderate fiber from drumstick, pumpkin, toor dal."
    ),
    "D19": Dish(
        dish_id="D19",
        name="Jowar Bhakri with Pithla (Gram Flour Curry) & Thecha",
        regional_origin="West India (Maharashtra/Rural)",
        category="Lunch/Dinner",
        serving_description="1 large sorghum flatbread (90g) + 120g besan pithla",
        serving_weight_g=240.0,
        calories_kcal=330.0,
        carbs_g=47.0,
        protein_g=11.2,
        fat_g=6.5,
        fiber_g=8.2,
        glycemic_index=50.0,
        glycemic_load=23.5,
        typical_swap_target=None,
        clinical_notes="Sorghum (jowar) is gluten-free with slow starch digestibility."
    ),
    "D20": Dish(
        dish_id="D20",
        name="Aloo Paratha (1 pc) with Butter & Curd",
        regional_origin="North India",
        category="Breakfast",
        serving_description="1 stuffed paratha (160g) + 1 pat butter (10g) + 100g curd",
        serving_weight_g=270.0,
        calories_kcal=460.0,
        carbs_g=56.0,
        protein_g=9.5,
        fat_g=21.0,
        fiber_g=4.5,
        glycemic_index=73.0,
        glycemic_load=40.9,
        typical_swap_target="D09",
        clinical_notes="Mashed potato stuffing wrapped in whole wheat pan-fried in fat."
    ),
    "D21": Dish(
        dish_id="D21",
        name="Appam (2 pcs) with Vegetable Stew",
        regional_origin="South India (Kerala)",
        category="Breakfast/Dinner",
        serving_description="2 fermented rice-coconut appams (140g) + 150ml coconut milk stew",
        serving_weight_g=290.0,
        calories_kcal=320.0,
        carbs_g=44.0,
        protein_g=5.2,
        fat_g=13.0,
        fiber_g=3.5,
        glycemic_index=65.0,
        glycemic_load=28.6,
        typical_swap_target=None,
        clinical_notes="Coconut milk medium-chain triglycerides slow peak absorption slightly."
    ),
    "D22": Dish(
        dish_id="D22",
        name="Dhokla (Khaman - 4 pcs) with Green Chutney",
        regional_origin="West India (Gujarat)",
        category="Snack/Breakfast",
        serving_description="4 steamed squares (140g) with mustard tempering + chutney",
        serving_weight_g=160.0,
        calories_kcal=220.0,
        carbs_g=32.0,
        protein_g=7.5,
        fat_g=6.0,
        fiber_g=3.2,
        glycemic_index=61.0,
        glycemic_load=19.5,
        typical_swap_target="D09",
        clinical_notes="Steamed gram flour snack. Often tempered with sugar syrup in commercial settings."
    ),
    "D23": Dish(
        dish_id="D23",
        name="Egg Bhurji (2 eggs) with 2 Multigrain Toasts",
        regional_origin="Urban Pan-India",
        category="Breakfast",
        serving_description="Scrambled eggs with onions, chilies (120g) + 2 slices toast (60g)",
        serving_weight_g=180.0,
        calories_kcal=315.0,
        carbs_g=28.0,
        protein_g=18.0,
        fat_g=14.0,
        fiber_g=4.2,
        glycemic_index=45.0,
        glycemic_load=12.6,
        typical_swap_target=None,
        clinical_notes="High biological value protein suppresses early glycemic spike."
    ),
    "D24": Dish(
        dish_id="D24",
        name="Samosa (1 pc) with Tamarind Chutney",
        regional_origin="Pan-India",
        category="Snack",
        serving_description="1 medium deep-fried samosa (90g) + 20g chutney",
        serving_weight_g=110.0,
        calories_kcal=290.0,
        carbs_g=36.0,
        protein_g=4.2,
        fat_g=16.0,
        fiber_g=2.1,
        glycemic_index=78.0,
        glycemic_load=28.1,
        typical_swap_target="D16",
        clinical_notes="Deep fried maida shell + boiled potatoes + sweetened chutney. High postprandial glucose spike."
    ),
    "D25": Dish(
        dish_id="D25",
        name="Sprouted Moong Salad (Sundal style with Lemon & Coconut)",
        regional_origin="Pan-India / South",
        category="Snack/Lunch",
        serving_description="1 bowl sprouted whole moong (150g) with cucumber, lemon, fresh coconut",
        serving_weight_g=160.0,
        calories_kcal=170.0,
        carbs_g=22.0,
        protein_g=11.5,
        fat_g=3.5,
        fiber_g=8.0,
        glycemic_index=32.0,
        glycemic_load=7.0,
        typical_swap_target=None,
        clinical_notes="Superb clinical choice. Sprouting boosts bioavailable micronutrients and dietary fiber."
    ),
}

def get_dish(dish_id: str) -> Optional[Dish]:
    """Retrieve dish by unique ID."""
    return INDIAN_THALI_REGISTRY.get(dish_id)

def get_all_dishes() -> List[Dish]:
    """Return all 25 registered dishes."""
    return list(INDIAN_THALI_REGISTRY.values())

def get_dishes_by_category(category: str) -> List[Dish]:
    """Filter dishes by meal category (Breakfast, Lunch/Dinner, Snack)."""
    return [d for d in INDIAN_THALI_REGISTRY.values() if d.category == category]

def calculate_glycemic_load(carbs_g: float, glycemic_index: float) -> float:
    """Calculate standard Glycemic Load (GL)."""
    return round((carbs_g * glycemic_index) / 100.0, 1)

def simulate_dish_macronutrients(dish: Dish, portion_factor: float = 1.0) -> Dict[str, float]:
    """
    Scale dish nutrients by user-selected portion size (e.g. 0.5x, 1.0x, 1.5x).
    Returns macronutrient vector compatible with the CGMacros feature space.
    """
    return {
        "calories": round(dish.calories_kcal * portion_factor, 1),
        "carbs": round(dish.carbs_g * portion_factor, 1),
        "protein": round(dish.protein_g * portion_factor, 1),
        "fat": round(dish.fat_g * portion_factor, 1),
        "fiber": round(dish.fiber_g * portion_factor, 1),
        "glycemic_load": round(dish.glycemic_load * portion_factor, 1),
        "glycemic_index": dish.glycemic_index,
    }
