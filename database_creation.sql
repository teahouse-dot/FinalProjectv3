---------------------- Script to build the MySQL database from npha csv file -----------------------------------------------
-- Uncomment and run code below if tables exist before running code below
-- DROP TABLE IF EXISTS npha_staging;
-- DROP TABLE IF EXISTS demographics_fact;
-- DROP TABLE IF EXISTS health_fact;
-- DROP TABLE IF EXISTS sleep_fact;
-- DROP TABLE IF EXISTS doctor_visit_dim;
-- DROP TABLE IF EXISTS age_dim;
-- DROP TABLE IF EXISTS health_dim;
-- DROP TABLE IF EXISTS employment_dim;
-- DROP TABLE IF EXISTS sleep_dim;
-- DROP TABLE IF EXISTS prescript_sleep_med_dim;
-- DROP TABLE IF EXISTS race_dim;
-- DROP TABLE IF EXISTS gender_dim;


-- create npha_staging table
-- The "Trouble Sleeping" column in the original csv file is excluded since its value range does not match the column description.
CREATE TABLE IF NOT EXISTS npha_staging (
    fact_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_visit INT,
    age INT,
    physical_health INT,
    mental_health INT,
    dental_health INT,
    employment INT,
    stress_sleep INT,
    med_sleep INT,
    pain_sleep INT,
    bathroom_sleep INT,
    unknown_sleep INT,
    prescript_sleep_med INT,
    race INT,
    gender INT);

INSERT INTO npha_staging (
    doctor_visit, 
    age, 
    physical_health, 
    mental_health,
    dental_health, 
    employment, 
    stress_sleep, 
    med_sleep,
    pain_sleep,
    bathroom_sleep,
    unknown_sleep,
    prescript_sleep_med,
    race,
    gender)
SELECT 
    `Number of Doctors Visited`,
    `Age`,
    `Phyiscal Health`,
    `Mental Health`,
    `Dental Health`,
    `Employment`,
    `Stress Keeps Patient from Sleeping`,
    `Medication Keeps Patient from Sleeping`,
    `Pain Keeps Patient from Sleeping`,
    `Bathroom Needs Keeps Patient from Sleeping`,
    `Uknown Keeps Patient from Sleeping`,
    `Prescription Sleep Medication`,
    `Race`,
    `Gender`
FROM npha_doctor_visits;

-- create age_dim table
CREATE TABLE IF NOT EXISTS age_dim (
    age_id INT PRIMARY KEY,
    age_desc VARCHAR(50) NOT NULL);
INSERT INTO age_dim (age_id, age_desc)
VALUES
(1, '50-64'),
(2, '65-80');

-- create employment_dim table
CREATE TABLE IF NOT EXISTS employment_dim (
    employment_id INT PRIMARY KEY,
    employment_desc VARCHAR(50) NOT NULL);

INSERT INTO employment_dim (employment_id, employment_desc)
VALUES
(-1, 'Refused'),
(1, 'Working full-time'),
(2, 'Working part-time'),
(3, 'Retired'),
(4, 'Not working at this time');

-- create race_dim table
CREATE TABLE IF NOT EXISTS race_dim (
    race_id INT PRIMARY KEY,
    race_desc VARCHAR(50) NOT NULL);

INSERT INTO race_dim (race_id, race_desc)
VALUES
(-2, 'Not asked'),
(-1, 'Refused'),
(1, 'White, Non-Hispanic'),
(2, 'Black, Non-Hispanic'),
(3, 'Other, Non-Hispanic'),
(4, 'Hispanic'),
(5, '2+ Races, Non-Hispanic');

-- create gender_dim table
CREATE TABLE IF NOT EXISTS gender_dim (
    gender_id INT PRIMARY KEY,
    gender_desc VARCHAR(50) NOT NULL);

INSERT INTO gender_dim (gender_id, gender_desc)
VALUES
(-2, 'Not asked'),
(-1, 'Refused'),
(1, 'Male'),
(2, 'Female');

-- create doctor_visit_dim table
CREATE TABLE IF NOT EXISTS doctor_visit_dim (
doctor_visit_id INT PRIMARY KEY, 
doctor_visit_desc VARCHAR(50) NOT NULL);

INSERT INTO doctor_visit_dim 
VALUES 
(1, '0-1 doctors'), 
(2, '2-3 doctors'), 
(3, '4 or more doctors'); 

-- Create health_dim table
CREATE TABLE IF NOT EXISTS health_dim (
health_id INT PRIMARY KEY, 
health_desc VARCHAR(50) NOT NULL);

INSERT INTO health_dim 
VALUES 
(-1, 'Refused'), 
(1, 'Excellent'), 
(2, 'Very Good'), 
(3, 'Good'), 
(4, 'Fair'), 
(5, 'Poor'); 

-- Create sleep_dim table
CREATE TABLE IF NOT EXISTS sleep_dim (
sleep_id INT PRIMARY KEY, 
sleep_desc VARCHAR(50) NOT NULL);

INSERT INTO sleep_dim (sleep_id, sleep_desc) 
VALUES 
(0, 'No'), 
(1, 'Yes');

-- Create prescript_sleep_med_dim table
CREATE TABLE IF NOT EXISTS prescript_sleep_med_dim (
prescript_sleep_med_id INT PRIMARY KEY, 
prescript_sleep_med_desc VARCHAR(50) NOT NULL); 

INSERT INTO prescript_sleep_med_dim (prescript_sleep_med_id, prescript_sleep_med_desc) 
VALUES 
(-1, 'Refused'), 
(1, 'Use regularly'), 
(2, 'Use occasionally'), 
(3, 'Do not use');


-- Preprocess npha_staging data to remove invalid values as defined in all sub dimensional tables.
-- Need to turn off SQL safe updates for the DELETE functions to work. Last line of code turns SQL safe updates back on. 
-- Invalid values exist in dental_health in the original dataset
SET SQL_SAFE_UPDATES = 0;
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM doctor_visit_dim WHERE doctor_visit = doctor_visit_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM age_dim WHERE age = age_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM health_dim WHERE physical_health = health_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM health_dim WHERE mental_health = health_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM health_dim WHERE dental_health = health_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM employment_dim WHERE employment = employment_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM sleep_dim WHERE stress_sleep = sleep_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM sleep_dim WHERE med_sleep = sleep_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM sleep_dim WHERE pain_sleep = sleep_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM sleep_dim WHERE bathroom_sleep = sleep_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM sleep_dim WHERE unknown_sleep = sleep_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM prescript_sleep_med_dim WHERE prescript_sleep_med = prescript_sleep_med_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM race_dim WHERE race = race_id);
DELETE FROM npha_staging WHERE NOT EXISTS (SELECT 1 FROM gender_dim WHERE gender = gender_id);
SET SQL_SAFE_UPDATES = 1;


-- create demographics_fact table 
CREATE TABLE IF NOT EXISTS demographics_fact (
fact_id INT PRIMARY KEY,
age_id INT NOT NULL,
employment_id INT NOT NULL,
race_id INT NOT NULL,
gender_id INT NOT NULL,
    
CONSTRAINT FK_age FOREIGN KEY (age_id) REFERENCES age_dim (age_id),
CONSTRAINT FK_employment FOREIGN KEY (employment_id) REFERENCES employment_dim (employment_id),
CONSTRAINT FK_race FOREIGN KEY (race_id) REFERENCES race_dim (race_id),
CONSTRAINT FK_gender FOREIGN KEY (gender_id) REFERENCES gender_dim (gender_id)
);

INSERT INTO demographics_fact (fact_id, age_id, employment_id, race_id, gender_id)
SELECT fact_id, age, employment, race, gender
FROM npha_staging;


-- Create health_fact table and connect keys to dimensional tables
CREATE TABLE IF NOT EXISTS health_fact (
fact_id INT PRIMARY KEY,  
doctor_visit_id INT NOT NULL, CONSTRAINT FK_doctor_visit FOREIGN KEY (doctor_visit_id) REFERENCES doctor_visit_dim (doctor_visit_id), 
physical_health_id INT NOT NULL, CONSTRAINT FK_physical_health FOREIGN KEY (physical_health_id) REFERENCES health_dim (health_id), 
mental_health_id INT NOT NULL, CONSTRAINT FK_mental_health FOREIGN KEY (mental_health_id) REFERENCES health_dim (health_id), 
dental_health_id INT NOT NULL, CONSTRAINT FK_dental_health FOREIGN KEY (dental_health_id) REFERENCES health_dim (health_id)
);

INSERT INTO health_fact (fact_id, doctor_visit_id, physical_health_id, mental_health_id, dental_health_id) 
SELECT fact_id, doctor_visit, physical_health, mental_health, dental_health
FROM npha_staging;


-- Create sleep_fact table
CREATE TABLE IF NOT EXISTS sleep_fact ( 
fact_id INT PRIMARY KEY, 
stress_sleep_id INT NOT NULL, 
med_sleep_id INT NOT NULL, 
pain_sleep_id INT NOT NULL, 
bathroom_sleep_id INT NOT NULL, 
unknown_sleep_id INT NOT NULL,  
prescript_sleep_med_id INT NOT NULL, 

CONSTRAINT FK_stress_sleep FOREIGN KEY (stress_sleep_id) REFERENCES sleep_dim(sleep_id), 
CONSTRAINT FK_med_sleep FOREIGN KEY (med_sleep_id) REFERENCES sleep_dim(sleep_id), 
CONSTRAINT FK_pain_sleep FOREIGN KEY (pain_sleep_id) REFERENCES sleep_dim(sleep_id), 
CONSTRAINT FK_bathroom_sleep FOREIGN KEY (bathroom_sleep_id) REFERENCES sleep_dim(sleep_id), 
CONSTRAINT FK_unknown_sleep FOREIGN KEY (unknown_sleep_id) REFERENCES sleep_dim(sleep_id), 
CONSTRAINT FK_prescript_sleep_med FOREIGN KEY (prescript_sleep_med_id) REFERENCES prescript_sleep_med_dim(prescript_sleep_med_id) 
); 

INSERT INTO sleep_fact ( 
fact_id, 
stress_sleep_id, 
med_sleep_id, 
pain_sleep_id, 
bathroom_sleep_id, 
unknown_sleep_id,  
prescript_sleep_med_id
 ) 
SELECT 
fact_id, 
stress_sleep, 
med_sleep, pain_sleep, 
bathroom_sleep, 
unknown_sleep, 
prescript_sleep_med 
FROM npha_staging;
