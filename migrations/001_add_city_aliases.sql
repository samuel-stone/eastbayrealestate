CREATE TABLE IF NOT EXISTS city_aliases (
    code TEXT PRIMARY KEY,
    city_name TEXT NOT NULL,
    state TEXT DEFAULT 'CA'
);

INSERT INTO city_aliases (code, city_name) VALUES
('OKLY','Oakley'),
('BAYPT','Bay Point'),
('RCHMD','Richmond'),
('ALAMO','Alamo'),
('ANT','Antioch'),
('SNRMN','San Ramon'),
('DAN','Danville'),
('MRTNZ','Martinez'),
('WALNUT CREEK','Walnut Creek'),
('CONCORD','Concord'),
('LAFAYETTE','Lafayette'),
('ORINDA','Orinda'),
('MORAGA','Moraga')
ON CONFLICT (code) DO UPDATE
SET city_name = EXCLUDED.city_name;
