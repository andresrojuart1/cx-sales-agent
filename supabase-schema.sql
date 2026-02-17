-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.ff_audience (
  CR_Code text NOT NULL,
  external_id text,
  name_requester text,
  company_email text,
  uid text UNIQUE,
  CONSTRAINT ff_audience_pkey PRIMARY KEY (CR_Code)
);
CREATE TABLE public.loan_fee_tiers (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  min_amount numeric NOT NULL,
  max_amount numeric NOT NULL,
  installments integer NOT NULL CHECK (installments = ANY (ARRAY[1, 2, 3])),
  fixed_fee numeric NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT loan_fee_tiers_pkey PRIMARY KEY (id)
);
CREATE TABLE public.quick_audience (
  external_id text,
  company_email text,
  client_requester text,
  name_requester text,
  CR_Code text NOT NULL,
  CL_Code text,
  CONSTRAINT quick_audience_pkey PRIMARY KEY (CR_Code)
);
CREATE TABLE public.quick_contract_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  contract_token text NOT NULL,
  document_name text,
  status_doc text,
  worker_name text,
  worker_email text,
  worker_status text,
  worker_signed_at timestamp with time zone,
  ontop_name text,
  ontop_email text,
  ontop_status text,
  ontop_signed_at timestamp with time zone,
  last_update timestamp with time zone,
  final_status text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT quick_contract_events_pkey PRIMARY KEY (id)
);
CREATE TABLE public.risk_matrix (
  des_email text NOT NULL,
  decision text DEFAULT 'Null'::text CHECK (decision = ANY (ARRAY['Approved'::text, 'Not approved'::text])),
  contractor_last_payment timestamp with time zone DEFAULT now(),
  actual_payment numeric DEFAULT '0'::numeric,
  id bigint NOT NULL DEFAULT nextval('risk_matrix_id_seq'::regclass),
  CONSTRAINT risk_matrix_pkey PRIMARY KEY (id)
);