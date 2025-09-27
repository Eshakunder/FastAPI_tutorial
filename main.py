from fastapi import FastAPI,Path ,HTTPException,Query #path() function and HTTPException check notes
from fastapi.responses import JSONResponse
import json
from pydantic import BaseModel,Field,computed_field
from typing import Annotated ,Literal,Optional

app = FastAPI()
class Patient(BaseModel):
    id:Annotated[str,Field(..., description="ID of the patient in the database",
                           examples=['P001'])]
    name:Annotated[str,Field(...,description="Name of the patient")]
    city:Annotated[str,Field(...,description="City of the patient")] 
    age:Annotated[int,Field(...,description="Age of the patient",gt=0,lt=120)]
    gender:Annotated[Literal['male', 'female', 'other'],Field(...,description="Gender of the patient")]
    height:Annotated[float,Field(...,description="Height of the patient in mtrs",gt=0)]
    weight:Annotated[float,Field(...,description="Weight of the patient in kgs",gt=0)]

    @computed_field
    @property
    def bmi(self) -> float:
        """Calculate the Body Mass Index (BMI) of the patient."""
        bmi = round(self.weight / (self.height ** 2), 2)
        return bmi
    
    @computed_field
    @property
    def verdict (self) -> str:
        """Determine the health status based on BMI."""
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"


class PatientUpdate(BaseModel):
    name:Annotated[Optional[str],Field(default=None)]
    city:Annotated[Optional[str],Field(default=None)] 
    age:Annotated[Optional[int],Field(default=None,gt=0)]
    gender:Annotated[Optional[Literal['male', 'female', 'other']],Field(default=None)]
    height:Annotated[Optional[float],Field(default=None,gt=0)]
    weight:Annotated[Optional[float],Field(default=None,gt=0)]



def data_load():
    """Load patient data from the JSON file."""

    with open('patients.json', 'r') as file:
        data = json.load(file)
    return data
# to get data from the server, we need to create a route .

def save_data(data):
    with open('patients.json', 'w') as f:
        json.dump(data, f)




@app.get('/') # if user visits the url ie http://localhost:8000 and enter
# / ie http://localhost:8000/ then this function will be called.
def hello():
    return {'message': 'Patient mangement system.'}
# to run the server, we need to use uvicorn
# command in the terminal: uvicorn main:app --reload
# --reload will automatically reload the server when we make changes to the code


@app.get('/about') # if user visits the url ie http://localhost:8000 and enter
# /about ie http://localhost:8000/about then this function will be called.
def about():
    return {'message': 'A fully functional API for patient management system.'}
# no need to reload the server after making changes to the code, as we are using --reload option in the uvicorn command.


@app.get('/view')
def view():
    data = data_load()
    return data


@app.get('/patient/{patient_id}')
def view_patient(patient_id:str = Path(...,description="ID of the patient in the database",
    example="P001")): #adding Path()function to get description and example of the parameter. In docs check 
    #decriptiona and example of the parameter.
    #load all the patients
    data = data_load()
    #find the patient with the given id
    if patient_id in data:
        return data[patient_id]
    #else:
        #return {'message': 'Patient not found.'} so instead of returning a message, we will raise an HTTPException
    raise HTTPException(status_code=404, detail="Patient not found")



#query parameters are used to filter the data based on the given field and order.
@app.get('/sort')
def sort_patients(sort_by:str = Query(..., description="Sort patients by weight , height and bmi "),
                  order:str= Query("asc",description="Order of sorting, either asc or desc",)):
    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail="Invalid field select from {valid_fields}")
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order, select either asc or desc")
    data = data_load()
    # sort the data based on the given field and order
    sorted_order = True if order=='desc' else False
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by,0), reverse=sorted_order)

    return sorted_data


@app.post('/create')
def create_patient(patient:Patient): # patient is the instance of the Patient model

    #load existing the data
    data = data_load()

    #check if the patient id already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient already exists.")
    
    #new patient add to the exsiting data , but existing data is dict and patient(new data ) is a pydantic object so convert it to dict.
    data[patient.id]=patient.model_dump(exclude=['id']) #patient with new id will be added to the data.

    #save the data to the json file
    save_data(data)
  
    return JSONResponse(status_code=201, content={"message": "Patient created successfully"})


@app.put('/edit/{patient_id}}')
def update_patient(patient_id:str,patient_update: PatientUpdate):

    data = data_load()
    #check if the patient id exists
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    #get the existing patient data
    existing_patient_info = data[patient_id]

    #convert the pydantic object to dict
    updated_patient_info = patient_update.model_dump(exclude_unset=True)
    #exclude_unset=True will exclude the fields that are not set in the patient_update object only the fields to be updated will be included.

    for key , value in updated_patient_info.items():#looping the fields given by the user to update.
        existing_patient_info[key] = value #updating the existing patient info with the new values.(eg: for city , mumbai in updated_patient_info, existing_patient_info['city'] = 'mumbai' it will be done like this)

        #but if height and weight are changed then bmi and verdict will also change
        #so we need to update the bmi and verdict fields as well.
        
        #first convert the existing_patient_info dict to pydantic object and validation is performed and new mbi everything will be converted.
        existing_patient_info['id'] = patient_id #since initally not including id
        #in exisiting_patient_id , so adding it.
        patient_pydantic_obj = Patient(**existing_patient_info)

        #then , form dictionary from pydantic object (vice versa as above)
        existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')#exclude id

        #add this dict to data
        data[patient_id] = existing_patient_info

        #save the data
        save_data(data)

        return JSONResponse(status_code=200,content={'message':'patient_updated'})
    
@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data = data_load()

    if patient_id not in data:
        raise HTTPException(status_code=404,detail='patient not found')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200,content={'message':'patient deleted'})