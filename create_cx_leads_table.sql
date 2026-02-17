-- Run this in Supabase SQL Editor to create the cx_leads table.

CREATE TABLE public.cx_leads (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    cr_code text NOT NULL,
    product text NOT NULL,
    agent_name text NOT NULL,
    agent_email text,
    notes text DEFAULT '',
    status text NOT NULL DEFAULT 'Qualified'
        CHECK (status IN ('Qualified', 'Contacted', 'Converted', 'Rejected')),
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT cx_leads_pkey PRIMARY KEY (id)
);

-- Index for duplicate-check lookups (cr_code + product + recent date)
CREATE INDEX idx_cx_leads_cr_product ON public.cx_leads (cr_code, product, created_at DESC);

-- Index for agent-filtered queries (email-based ownership)
CREATE INDEX idx_cx_leads_agent_email ON public.cx_leads (agent_email, created_at DESC);

-- Index for legacy agent-name queries (fallback for pre-auth leads)
CREATE INDEX idx_cx_leads_agent ON public.cx_leads (agent_name, created_at DESC);
