-- Quick transactions: they tell us if a client has already asked for a quick loan
SELECT DISTINCT
    wt.id_transaction AS id_wallet,
    wt.dat_transaction,
    CASE 
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE c.cod_contractor
    END AS cod_contractor,
    wt.des_transaction_type,
    wt.amt_transaction,
    msg.message, wt.id_original_wallet_transaction 
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj
    ON msgj.wallet_transaction_id = wt.id_transaction
LEFT JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
LEFT JOIN raw_data.raw_ops_top_up_upload msg
    ON msg.id = msgj.ops_top_up_upload_id
LEFT JOIN internal.lkp_contractor_pii pi 
    ON pi.hash_cod_contractor = wt.cod_contractor
WHERE 
    (
        msg.message ILIKE 'Quick%' OR  
        wt.des_transaction_type ILIKE 'Quick%'
    )
    OR wt.id_transaction IN (
        '1989950', '1989951', '1989952', '2004982', '2004981',
        '1989953', '2004980', '1989954', '2003004', '2012763',
        '2012768', '2012771', '2012764', '2012775', '2012767',
        '2012769', '2012765', '2012773', '2012776', '2012770',
        '2012772', '2012778', '2012766', '2025755', '2025754',
        '2012777'
    )
ORDER BY wt.dat_transaction;

-- Future Fund transactions: they tell us if a client has already invested in Future Fund
SELECT
  wt.id_transaction,
  wt.dat_transaction,
  CASE 
    WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
    ELSE wt.cod_contractor
  END AS cod_contractor,
  wt.des_transaction_type,
  wt.amt_transaction,
  msg.message
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj 
  ON msgj.wallet_transaction_id = wt.id_transaction
LEFT JOIN raw_data.raw_ops_top_up_upload msg 
  ON msg.id = msgj.ops_top_up_upload_id
LEFT JOIN internal.lkp_contractor_pii pi 
  ON pi.hash_cod_contractor = wt.cod_contractor
WHERE BTRIM(msg.message) ILIKE 'future%'   -- empieza con "future", case-insensitive
ORDER BY wt.dat_transaction DESC, wt.id_transaction DESC;

-- Tapi transactions: they tell us if a client has already paid a bill via Tapi
SELECT DISTINCT
    wt.id_transaction AS id_wallet,
    wt.dat_transaction,
    CASE 
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE c.cod_contractor
    END AS cod_contractor,
    wt.des_transaction_type,
    wt.amt_transaction
    FROM process_data.wallet_transaction wt
LEFT JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
LEFT JOIN internal.lkp_contractor_pii pi 
    ON pi.hash_cod_contractor = wt.cod_contractor
where wt.des_transaction_type = 'UTILITIES_PAYMENT'
ORDER BY wt.dat_transaction;

--Tapi segment: they tell us if a client is eligible for the Tapi service

select
CASE   WHEN pi.cod_contractor IS NOT NULL THEN pi.des_email ELSE C.des_email END AS des_email ,
CASE   WHEN pi.cod_contractor IS NOT NULL THEN pi.full_name ELSE C.full_name END AS full_name,
CASE   WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor ELSE C.cod_contractor END AS cod_contractor  ,
C.des_residence_country  from process_data.contractor c
  LEFT JOIN internal.lkp_contractor_pii pi 
  ON pi.hash_cod_contractor = C.cod_contractor
  left join process_Data.contract c2 on c2.id_contractor =  c.id_contractor 
where c.COD_residence_country in ('COL','MEX','ARG','PER','CHL') 
and c2.des_state in('ACTIVE')


-- eSim transactions: they tell us if a client has already bought an eSim
select
wt.id_transaction ,
    wt.dat_transaction ,
    CASE   WHEN pi.cod_contractor 
    IS NOT NULL THEN pi.cod_contractor ELSE wt.cod_contractor end
    AS cod_contractor,
wt.des_transaction_type ,
wt.amt_transaction ,
msg.message
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj
    ON msgj.wallet_transaction_id = wt.id_transaction
LEFT JOIN raw_data.raw_ops_top_up_upload msg
    ON msg.id = msgj.ops_top_up_upload_id
     LEFT JOIN internal.lkp_contractor_pii pi 
  ON pi.hash_cod_contractor = wt.cod_contractor
WHERE msg.message IS NOT NULL
  AND (
        msg.message IN (
            'E-sim',
            'E-sim Debit',
            'Esim Refund',
            'Esim Return',
            'Esim Debit'
        ))

-- Reserve audience: they tell us if a client is elegible for the Reserve Program but has not enrolled yet
select DISTINCT  CASE 
    WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
    ELSE C.cod_contractor
  END AS cod_contractor  from process_data.plan_subscription ps
left join PROCESS_dATA.contractOR C on C.id_contractor  = PS.id_contractor 
LEFT JOIN internal.lkp_contractor_pii pi 
  ON pi.hash_cod_contractor = C.cod_contractor
where ps.is_enabled =true and cod_plan ='RESERVE'

-- Contractor: this table is the source of truth for the contractors. you can use this table to get the contractor information.
-- process_data.contractor definition

-- Drop table

-- DROP TABLE process_data.contractor;

--DROP TABLE process_data.contractor;
CREATE TABLE IF NOT EXISTS process_data.contractor
(
	id_contractor INTEGER   ENCODE az64
	,cod_contractor VARCHAR(36)   ENCODE lzo
	,id_entity INTEGER   ENCODE az64
	,id_person INTEGER   ENCODE az64
	,first_name VARCHAR(288)   ENCODE lzo
	,last_name VARCHAR(288)   ENCODE lzo
	,full_name VARCHAR(577)   ENCODE lzo
	,des_document_number VARCHAR(90)   ENCODE lzo
	,des_document_type VARCHAR(192)   ENCODE lzo
	,dat_birth DATE   ENCODE az64
	,num_age BIGINT   ENCODE az64
	,dat_first_top_up TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,cod_residence_country_region VARCHAR(30)   ENCODE lzo
	,des_residence_country_region VARCHAR(900)   ENCODE lzo
	,cod_residence_country VARCHAR(9)   ENCODE lzo
	,des_residence_country VARCHAR(240)   ENCODE lzo
	,is_residence_country_restricted INTEGER   ENCODE az64
	,des_residence_state VARCHAR(225)   ENCODE lzo
	,des_residence_city VARCHAR(576)   ENCODE lzo
	,des_residence_address VARCHAR(576)   ENCODE lzo
	,cod_residence_zip VARCHAR(96)   ENCODE lzo
	,cod_nationality_country_region VARCHAR(30)   ENCODE lzo
	,des_nationality_country_region VARCHAR(900)   ENCODE lzo
	,cod_nationality_country VARCHAR(9)   ENCODE lzo
	,des_nationality_country VARCHAR(240)   ENCODE lzo
	,is_us_person BOOLEAN   ENCODE RAW
	,des_gender VARCHAR(1147)   ENCODE lzo
	,des_email VARCHAR(49152)   ENCODE lzo
	,dat_app_downloaded TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,id_dial_code INTEGER   ENCODE az64
	,des_phone VARCHAR(96)   ENCODE lzo
	,cod_dial INTEGER   ENCODE az64
	,des_legal_name VARCHAR(576)   ENCODE lzo
	,des_trade_name VARCHAR(450)   ENCODE lzo
	,des_contractor_type VARCHAR(144)   ENCODE lzo
	,is_tos_accepted INTEGER   ENCODE az64
	,cod_external_kyc_check VARCHAR(450)   ENCODE lzo
	,des_kyc_check_status VARCHAR(135)   ENCODE lzo
	,dat_last_kyc_check TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,des_validation_provider_name VARCHAR(225)   ENCODE lzo
	,num_contracts BIGINT   ENCODE az64
	,num_contracts_in_active_state BIGINT   ENCODE az64
	,num_active_contracts BIGINT   ENCODE az64
	,has_active_contract INTEGER   ENCODE az64
	,has_compensation_in_last_months INTEGER   ENCODE az64
	,has_compensation_in_last_month INTEGER   ENCODE az64
	,has_spending_in_60_days INTEGER   ENCODE az64
	,dat_first_compensation DATE   ENCODE az64
	,is_receiving_compensation_wallet INTEGER   ENCODE az64
	,amt_monthly_compensation_usd NUMERIC(38,2)   ENCODE az64
	,has_card INTEGER   ENCODE az64
	,has_positive_card_balance INTEGER   ENCODE az64
	,amt_card_balance NUMERIC(38,2)   ENCODE az64
	,dat_card_activation TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,has_cashout_in_60_days_fs INTEGER   ENCODE az64
	,has_positive_wallet_balance INTEGER   ENCODE az64
	,amt_wallet_balance NUMERIC(38,6)   ENCODE az64
	,amt_avg_wallet_balance NUMERIC(35,2)   ENCODE az64
	,is_ontoper INTEGER   ENCODE az64
	,dat_creation TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,id_creator INTEGER   ENCODE az64
	,has_ontop_pay INTEGER   ENCODE az64
	,id_tax VARCHAR(120)   ENCODE lzo
	,des_physical_card_status VARCHAR(24000)   ENCODE lzo
	,dat_physical_card_activation TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,num_withdrawals BIGINT   ENCODE az64
	,is_active_contractor INTEGER   ENCODE az64
	,is_active_wallet_fs INTEGER   ENCODE az64
	,des_wallet_status VARCHAR(11)   ENCODE lzo
	,dat_wallet_creation TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,dat_wallet_exclusion TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,dat_processing TIMESTAMP WITH TIME ZONE   ENCODE az64
	,new_has_card_physical BIGINT   ENCODE az64
	,new_has_card_virtual BIGINT   ENCODE az64
	,new_dat_card_activation_virtual TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,new_dat_card_activation_physical TIMESTAMP WITHOUT TIME ZONE   ENCODE az64
	,new_des_physical_card_status VARCHAR(256)   ENCODE lzo
	,document_expiration_date DATE   ENCODE az64
	,picture_front_side_id INTEGER   ENCODE az64
	,picture_back_side_id INTEGER   ENCODE az64
	,tmp_wbalance_man NUMERIC(38,6)   ENCODE az64
)
DISTSTYLE AUTO
 DISTKEY (id_contractor)
;
ALTER TABLE process_data.contractor owner to awsuser;