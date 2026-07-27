-- Script d'initialisation PostgreSQL pour le projet PlagiatDetect
-- Exécuter avec: psql -U postgres -f init_db.sql

CREATE DATABASE plagiat_db;
CREATE USER plagiat_user WITH PASSWORD 'plagiat_secure_pass_2024';
GRANT ALL PRIVILEGES ON DATABASE plagiat_db TO plagiat_user;
ALTER USER plagiat_user CREATEDB;

\c plagiat_db;

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
