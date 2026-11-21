-- CreditLens SQL analysis
-- Run against SQLite database data/processed/creditlens.db.
-- Table: credit_customers

-- 1. Portfolio overview
SELECT COUNT(*) AS customers,
       SUM(default_flag) AS defaults,
       ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct,
       ROUND(AVG(limit_bal), 2) AS avg_credit_limit
FROM credit_customers;

-- 2. Default rate by credit limit segment
SELECT credit_limit_segment, COUNT(*) AS customers,
       ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM credit_customers
GROUP BY credit_limit_segment
ORDER BY default_rate_pct DESC;

-- 3. Default rate by repayment behavior
SELECT repayment_segment, COUNT(*) AS customers,
       ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM credit_customers
GROUP BY repayment_segment
ORDER BY default_rate_pct DESC;

-- 4. High utilization customers (screening analysis only)
SELECT id, limit_bal, bill_amt1, credit_utilization_pct, default_flag
FROM credit_customers
WHERE credit_utilization_pct >= 80
ORDER BY credit_utilization_pct DESC
LIMIT 100;

-- 5. Window function: rank customers by utilization within credit segment
SELECT id, credit_limit_segment, credit_utilization_pct,
       RANK() OVER (
         PARTITION BY credit_limit_segment
         ORDER BY credit_utilization_pct DESC
       ) AS utilization_rank
FROM credit_customers;

-- 6. CTE: aggregate customer repayment history
WITH repayment AS (
  SELECT id, default_flag,
         (CASE WHEN pay_0 > 0 THEN 1 ELSE 0 END +
          CASE WHEN pay_2 > 0 THEN 1 ELSE 0 END +
          CASE WHEN pay_3 > 0 THEN 1 ELSE 0 END +
          CASE WHEN pay_4 > 0 THEN 1 ELSE 0 END +
          CASE WHEN pay_5 > 0 THEN 1 ELSE 0 END +
          CASE WHEN pay_6 > 0 THEN 1 ELSE 0 END) AS delayed_months
  FROM credit_customers
)
SELECT delayed_months, COUNT(*) AS customers,
       ROUND(AVG(default_flag) * 100, 2) AS default_rate_pct
FROM repayment
GROUP BY delayed_months
ORDER BY delayed_months;
