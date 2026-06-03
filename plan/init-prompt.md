---

# Meal Planner LLM Project Specification

## Goal

Create a meal planner that plans meals for the next 7 days for the user and outputs the necessary grocery list. The user will interact and chat with this LLM directly within this repository.

---

## Use Cases

### Use Case 1: Generate 7-Day Meal Plan and Grocery List

* Create a complete meal plan for a full week.
* Generate a comprehensive grocery list based on the meal plan.
* Track calories and nutritional information for each meal.

### Use Case 2: Update and Regenerate

* Regenerate the remainder of the week's meal plan based on user updates.
* Automatically update the grocery list to reflect changes.
* Updates may include current grocery supplies, changing activity plans, fitness activities, eating out, etc.

---

## Implementation Notes

* **Knowledge Base:** The LLM will utilize the stored `.md` files in this project repository to inform its decision-making and recommendations to the user.
* **Web Search:** The LLM should use the internet to research/estimate nutritional information and source ideas for cheap, healthy meals.
* **State Management:**
* Use a JSON state file for persisting current user inventory, current day of the week, etc.
* Use a separate JSON state file to track the current running meal plan.
* Use Markdown (`.md`) files for persisting static rules and data models.


* **Updates Handling:** The active meal plan will be saved as an outputted Markdown file in the repo. This file will be completely rewritten whenever the user requests a plan regeneration.

---

## System Requirements & Rules

### Core Rules for Meal Planning

* **Dinner Drink:** Include one glass of 1% milk with dinner every day.
* **Calorie Limits:**
* **Standard Days:** Total daily intake must be a hard cap under **2,250 calories**.
* **Pre-Long Run Day:** The day before the long run can increase to **2,500–2,700 calories**.


* **Grocery Budget & Simplicity:**
* Focus on cheap, everyday grocery items available at any standard store.
* Meal repetition across days is highly encouraged to keep the grocery list simple.
* **Proteins:** Recommend at max 3 large proteins per week (e.g., ground beef, chicken thigh, chicken breast). *Note: Eggs do not count toward this limit.*
* **Vegetables:** Recommend at max 4–5 distinct vegetables per week (e.g., cabbage, mushrooms, spinach, bell peppers).
* **Grains:** Hard locked to **white rice**, **quinoa**, and **oatmeal** only.


* **Meal Structure:**
* **Breakfast:** Always skipped.
* **Lunch:** Must be very simple. It should only require basic mixing/combining or reheating small leftovers.


* **Batch Cooking (Leftover Logic):**
* Recommend meal plans where cooking can be done in advance for multiple meals.
* *Example:* If lunch and dinner both involve chicken, cook an extra portion during dinner so it can be eaten for the following day's lunch. Alternate proteins tactically to avoid exact consecutive meal burnout.



### User Profile & Fitness Goals

* **Demographics:** 6 feet 1 inch, 186 pounds.
* **Goal:** Lose fat while gaining or maintaining muscle. Calories and macros must align with this plan.
* **Activity Level:** Very active lifestyle.
* **Weightlifting:** Small weightlifting sessions every other day.
* **Running Schedule (4 runs per week):**
* **Monday:** Easy run
* **Wednesday:** Tempo / Hard run
* **Thursday:** Easy run
* **Saturday:** Long run




* **TDEE Calculation:** Use the standard Mifflin-St. Jeor formula.
* *User Running Calibration Reference:* 18 miles = 1,500 calories burned; 16 miles = 2,200 calories burned; 3.15 miles = 417 calories burned; 7.51 miles = 987 calories burned.
* *Adjustment:* Slightly increase carbohydrates and adjust meals in the direct lead-up to the Saturday long run to prevent energy depletion.



---

## Data Models & Repository Files

### 1. `foods_i_like.md`

This file serves as the source of truth for ingredients the LLM can use. It must be a well-formatted markdown table.

> ⚠️ **LLM Rule:** If an ingredient's macros are missing, flag it clearly in the user interface so the user can update the file with exact values over time.

| Ingredient Category | Item Name | Calories | Protein (g) | Carbs (g) | Fat (g) | Notes / Preferences |
| --- | --- | --- | --- | --- | --- | --- |
| **Proteins** | Chicken Thighs |  |  |  |  | User favorite |
| **Proteins** | Chicken Breast |  |  |  |  | User favorite |
| **Proteins** | Ground Beef |  |  |  |  | User favorite |
| **Proteins** | High Protein Tofu |  |  |  |  | User favorite |
| **Vegetables** | Broccoli |  |  |  |  |  |
| **Vegetables** | Cucumber |  |  |  |  |  |
| **Vegetables** | Onions |  |  |  |  | Loves them (grilled, sauteed, red pickled) |
| **Vegetables** | Cherry Tomatoes |  |  |  |  |  |
| **Vegetables** | Cabbage |  |  |  |  |  |
| **Vegetables** | Mushrooms |  |  |  |  |  |
| **Vegetables** | Sauteed Spinach |  |  |  |  |  |
| **Grains** | Oatmeal |  |  |  |  | In pantry |
| **Fruit** | Blueberries |  |  |  |  | For lunch |
| **Fruit** | Banana |  |  |  |  | For lunch |
| **Dairy** | Fat-Free Greek Yogurt |  |  |  |  | For lunch (with berries & banana) |
| **Pantry / Supplements** | Orgain Plant Protein | 150 | 21g |  |  | 2 scoops. Okay to recommend >1 serving/day |
| **Pantry / Condiments** | Gochujang |  |  |  |  | Likes making sauces with it |

### 2. Output Format Requirements (`meal_plan_output.md`)

When presenting the generated plan to the user, the LLM must output the result in a **Markdown code block** (or the easiest format for other LLMs to parse) following this strict structure:

#### Part 1: Weekly Schedule

Provide a daily breakdown starting on Sunday. Each day must include:

* Meal selections for Lunch and Dinner.
* Text comments explaining leftover logic (e.g., *"Cook extra ground beef tonight to use for Tuesday's lunch"*).
* A caloric and macro summary (Calories, Protein, Carbs) broken down per meal.

#### Part 2: Grocery List Table

A consolidated markdown table categorized as follows:

| Category | Item Name | Quantity | Notes |
| --- | --- | --- | --- |
| **Proteins** | Chicken breast, Ground beef |  |  |
| **Vegetables** | Broccoli, Cucumber, Onions, Cherry tomatoes |  |  |
| **Grains** | Oatmeal, White rice, Quinoa |  |  |
| **Dairy** | 1% milk, Fat-free Greek yogurt, Cottage cheese, Cheese |  |  |
| **Fruits** | Bananas, Apples, Blueberries |  |  |
| **Pantry** | Peanut butter, Orgain plant protein powder, Granola, Spices |  |  |

---

## Clarifying Q&A and Corner Cases

### LLM Context & State Persistence

**Question:** How does the LLM access the `.md` files in the repository? Is this a local file system read, a vector database lookup, or a specific API endpoint?

* **Answer:** This is a local file system read. The user will open this repository and use the integrated LLM chat feature. The LLM will have direct access to the project directory and its files.

**Question:** Where is the "state" stored? The prompt mentions "stored .md files" for the plan, but `.md` files are static. How does the LLM persist the current grocery list, current inventory, or current day of the week? Is there a JSON state file, a database, or does the LLM maintain a "context window" of the current plan within the chat session?

* **Answer:**
* Use a JSON state file for persisting dynamic, current data (e.g., current inventory, current day of the week).
* Use a separate JSON state file to track the active running meal plan.
* Use Markdown (`.md`) files to persist static states, rules, and user preferences.



**Question:** How does the LLM handle "updates" (e.g., "I ate out today")? Does it rewrite the `.md` files, or does it generate a new plan based on a new prompt that includes the history?

* **Answer:** The active meal plan will be persisted as an outputted Markdown file saved directly in this repository. This file will be completely rewritten whenever the user requests a modification or a full plan regeneration.

---

### Nutritional Constraints & Data Source

**Question:** The prompt states "The LLM should use the internet to research/estimate the nutritional information." Does the LLM have access to a live browsing tool? If yes, which API (e.g., Tavily, Serper)? If no, how will it source data?

* **Answer:** The LLM can utilize the IDE extension's web context capabilities. To trigger a live web search, the LLM must format its internal requests explicitly like: `"Using the attached @Web context..."` (complying with the continue.dev extension standard).

**Question:** Specific macros were provided for "Orgain plant protein" (150 cal, 21g protein). Does the LLM have access to a database for the other ingredients (e.g., specific cut of chicken, specific brand of oatmeal), or must the user provide these values?

* **Answer:** The user will provide these exact macro values over time. The LLM's role is to proactively flag any ingredient in the file where macro data is missing, alerting the user to input the missing values.

**Question:** Is the 2,250-calorie limit a hard cap per day, or an average over the week?

* **Answer:** It is a hard cap per day. The only exception is the day directly leading up to the Saturday long run, where the daily cap can be increased to **2,500–2,700 calories** to support energy demands.

**Question:** How does the LLM calculate TDEE (Total Daily Energy Expenditure) given the specific running schedule (Easy, Tempo, Long) and weightlifting? Do we use a standard formula (Mifflin-St. Jeor) or a specific calculator?

* **Answer:** Use the standard **Mifflin-St. Jeor** formula. For calorie calibration, use the user's real-world running data as a benchmark reference:
* 18 miles = 1,500 calories burned
* 16 miles = 2,200 calories burned
* 7.51 miles = 987 calories burned
* 3.15 miles = 417 calories burned



---

### Data Models & Schema

**Question:** What is the expected structure for the "Foods that I like" markdown file? Should the LLM parse the text, or should the user format it as a specific schema (e.g., YAML, JSON, or a specific Markdown table) to ensure accurate macro extraction?

* **Answer:** The data must be structured as a standard Markdown table. The LLM will reference this structural layout to accurately parse ingredients and extract macro data.

**Question:** What is the format for the "Grocery List"? A simple text list, CSV, or a specific Markdown table with dedicated columns?

* **Answer:** It must be formatted strictly as a structured Markdown table divided by ingredient categories.

---

### Regeneration & Output Logic

**Question:** When "regenerating the remainder of the week," what is the trigger? Does the LLM simply continue the pattern, or does it require a specific command (e.g., `/regenerate`) and a summary of what changed?

* **Answer:** The user will prompt the LLM by explicitly stating the current day of the week and providing a query outlining what needs to change (e.g., *"Today is Tuesday and I am eating out tonight"*). If the user requests a change but forgets to specify the current day or context, the LLM must prompt the user for these details before running the regeneration.

**Question:** Should the LLM output the plan inside a Markdown code block with a specific template, or as plain text?

* **Answer:** The LLM must output the plan inside a **Markdown code block** (or an identical clean format) so that it remains easily readable and highly parseable for other LLMs down the line.

**Question:** How should the LLM handle the "instructions on when to make more" (leftover logic)? Is this a text comment in the plan, or a structured section?

* **Answer:** It should be written as a natural **text comment** inline with the meal plan schedule.