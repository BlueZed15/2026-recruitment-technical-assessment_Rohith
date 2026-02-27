from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str
	type: str

	@classmethod
	def cookbookentry_check_init(cls,data:dict):
		name_field=data.get("name")	
		if not isinstance(name_field, str):
			return None			
		
		return cls(name=parse_handwriting(name_field),type=data.get("type"))

@dataclass
class RequiredItem():
	name: str
	quantity: int
	
	@classmethod
	def requireditem_check_init(cls,data:dict):
		name_field=data.get("name")
		quantity_field=data.get("quantity")
		if not isinstance(name_field,str) or not isinstance(quantity_field,int):
			return None
		
		return cls(name=parse_handwriting(name_field),quantity=quantity_field)

@dataclass
class Recipe(CookbookEntry):
	requiredItems: List[RequiredItem]

	@classmethod
	def recipe_check(cls,data:dict):
		cookbookentry_obj=CookbookEntry.cookbookentry_check_init(data)
		if not cookbookentry_obj:
			return None
		
		required_items_field = data.get("requiredItems", [])
		if not isinstance(required_items_field, list):
			return None

		items = []
		item_names=[]
		for item_dict in required_items_field:
			if not isinstance(item_dict,dict):
				return None
			
			item = RequiredItem.requireditem_check_init(item_dict)
			item_name=item.name
			if not item or item_name in item_names:
				return None
			
			items.append(item)
			item_names.append(item_name)

		return cls(**cookbookentry_obj.__dict__, requiredItems=items)

@dataclass
class Ingredient(CookbookEntry):
	cookTime: int

	@classmethod
	def ingredient_check_init(cls,data:dict):
		cookbookentry_obj=CookbookEntry.cookbookentry_check_init(data)
		if not cookbookentry_obj:
			return None
		
		
		cook_time_field=data.get('cookTime')
		if not isinstance(cook_time_field,int) or cook_time_field<0:
			return None
		
		return Ingredient(**cookbookentry_obj.__dict__,cookTime=cook_time_field)
		

# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook=[]
cookbook_dataframe=pd.DataFrame(columns=["name","type","requiredItems","cookTime"])
cookbookentry=[]

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	# TODO: implement me	
	temp_str=re.sub(r"[\s_-]"," ",recipeName)
	recipeName=re.sub(r"[^\w ]|[\d]","",temp_str)
	
	return recipeName.title() if recipeName else None
	#return recipeName


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	# TODO: implement me
	data=request.get_json()
	type_field=data.get("type")
	entry=None
	
	if type_field=="ingredient":
		entry=Ingredient.ingredient_check_init(data)
	elif type_field=="recipe":
		entry=Recipe.recipe_check(data)
	

	if entry!=None and entry.name not in cookbookentry:
		cookbook.append(entry)
		newrow1={**entry.__dict__,"type":type_field}
		
		global cookbook_dataframe
		cookbook_dataframe=pd.concat([cookbook_dataframe,pd.DataFrame([newrow1])],ignore_index=True)
		cookbookentry.append(entry.name)
		

		return "",200
	else:
		return jsonify({'message': "Invalid Entry. Was not added to cookbook."}), 400

	#return 'not implemented', 500


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	# TODO: implement me
	name_input=parse_handwriting(request.args.get("name",None,type=str))
	if not name_input or name_input not in cookbook_dataframe.loc[cookbook_dataframe["type"]=="recipe","name"].values:
		return jsonify({"message":"invalid input"}),400
	
	ingredients=return_items(cookbook_dataframe[cookbook_dataframe["name"]==name_input]["requiredItems"].values[0],1)
	if not ingredients:
		return jsonify({"message":"certains ingredient/requireditem names are not in cookbook"}),400
	
	return jsonify({"name":name_input}|ingredients),200
	#return 'not implemented', 500

def return_items(required_items:list[RequiredItem],prev_quantity:int):
	total_cooktime=0
	ingredients=[]
	for item in required_items:
		name=item.name
		quantity=item.quantity

		item_row= cookbook_dataframe[cookbook_dataframe["name"]==name]
		if item_row.empty:
			return None
				
		if item_row["type"].values[0]=="ingredient":
			total_cooktime+=quantity*item_row["cookTime"].values[0]
			ingredients.append(RequiredItem(name,quantity*prev_quantity).__dict__)
		else:
			temp=return_items(item_row["requiredItems"].values[0],quantity*prev_quantity)
			if not temp:
				return None
			total_cooktime+=quantity*temp["cookTime"]
			ingredients.extend(temp["ingredients"])
	
	return {"cookTime":total_cooktime,"ingredients":ingredients}



# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
