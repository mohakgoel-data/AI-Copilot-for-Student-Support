SELECT id,
       filename,
       created_at,
       file_hash
FROM public.documents
LIMIT 1000;