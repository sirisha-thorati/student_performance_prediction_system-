import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle

# Load dataset
data = pd.read_csv("student_data.csv")

# Encode Pass/Fail
data['Pass_Fail'] = data['Pass_Fail'].map({'Pass':1,'Fail':0})

# Encode Grade & Skill
le_grade = LabelEncoder()
le_skill = LabelEncoder()

data['Grade'] = le_grade.fit_transform(data['Grade'])
data['Skill_Level'] = le_skill.fit_transform(data['Skill_Level'])

# Features
X = data[['Subject1','Subject2','Subject3','Subject4','Subject5','Subject6','Average_Marks']]
y = data['Pass_Fail']

# Split data
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

# Train model
model = RandomForestClassifier()
model.fit(X_train,y_train)

# Save model
pickle.dump(model,open("student_model.pkl","wb"))

print("Model trained and saved successfully")