-- Migrazione 0013: toglie dallo schema i valori di policy dei profili di peso.
-- Si applica dopo la 0012. schema.sql dava default a lambda_r (0.5), theta_n e theta_d
-- (0.50): erano soglie scritte nello schema. Ora ogni profilo deve dichiararle,
-- e le approva il comitato guida con il profilo.

ALTER TABLE weight_profiles
  ALTER COLUMN lambda_r DROP DEFAULT,
  ALTER COLUMN theta_n DROP DEFAULT,
  ALTER COLUMN theta_d DROP DEFAULT;
