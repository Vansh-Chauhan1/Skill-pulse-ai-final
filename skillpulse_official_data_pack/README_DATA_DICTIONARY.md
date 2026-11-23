# SkillPulse AI — Official-source data pack (PLFS + NCS)

Reference period: PLFS July 2023–June 2024 and NCS financial year 2023–24.
This pack is a manually transcribed, source-attributed starter dataset. The values below are report values, not synthetic estimates.

## Files

### `raw/plfs/plfs_state_wpr_2023_24.csv`
- Source: MoSPI/NSSO, Annual Report PLFS 2023–24, Appendix A, Table 17, pages A-67 to A-68.
- Indicator: Worker Population Ratio (WPR), usual status (principal + subsidiary, ps+ss), all ages.
- Values are percentages, not worker headcounts.
- `rural_urban_person_wpr_pct` is the combined rural+urban person value. Male/female and rural/urban breakdowns are retained.
- Chandigarh rural values are blank in the source table; blank is not zero.

### `raw/plfs/plfs_all_india_industry_distribution_2021_24.csv`
- Source: MoSPI/NSSO, Annual Report PLFS 2023–24, Statement 7, report page 14.
- Indicator: Percentage distribution of workers in usual status (ps+ss) by broad NIC-2008 industry division, all India.
- Includes 2021–22, 2022–23 and 2023–24 for a limited descriptive time series.
- These are shares of employed workers, not vacancy demand or numbers of workers.
- Rural+urban person values are in `rural_urban_person_pct`.

### `raw/ncs/ncs_sector_vacancies_fy2022_23_fy2023_24.csv`
- Source: National Career Service, Comparative NCS Statistics FY 2022–23 and FY 2023–24, sector-wise vacancies table.
- Values are vacancies mobilised through the NCS platform as reported, not a census of all vacancies in India.
- The table reports nine sector categories. Do not assume these nine rows sum to the NCS headline total; the published sector table does not show a complete reconciliation.

### `raw/ncs/ncs_qualification_vacancies_fy2022_23_fy2023_24.csv`
- Source: same NCS comparative statistics report, qualification-wise vacancies table.
- Categories and values are retained as published.

### `raw/ncs/ncs_summary_statistics_fy2022_23_fy2023_24.csv`
- Source: same NCS comparative statistics report, headline metrics table.

## Critical interpretation rules

1. Do NOT convert PLFS WPR percentages into `available_workers` without a defensible state population denominator for the same geography, age universe, reference period and rural/urban coverage.
2. Do NOT subtract PLFS WPR percentages from NCS vacancy counts. They are different units and different statistical universes.
3. NCS vacancies mobilised are vacancies recorded/mobilised on the NCS portal, not the complete Indian labour-market demand.
4. PLFS broad industry sections use NIC-2008, while NCS sector labels are portal categories. They need an explicit, documented crosswalk before sector comparisons.
5. These source files must remain separate from the prototype `employment_data.csv` until a defensible harmonisation pipeline is implemented. Do not overwrite the current file with these datasets.
6. The existing prototype fields `state, industry, skill, demand, available_workers` cannot be accurately populated from these summary tables alone. A true skill-level gap requires aligned occupation/skill demand and supply data, compatible dates and geographies, and documented mapping assumptions.

## Sources

- PLFS Annual Report 2023–24 (July 2023–June 2024): https://mospi.gov.in/sites/default/files/publication_reports/AnnualReport_PLFS2023-24L2.pdf
- NCS Comparative Statistics FY 2022–23 and FY 2023–24: https://www.ncs.gov.in/Documents/NCS-Statistics-2022-23-24.pdf

## Suggested placement in the SkillPulse repository

Copy the `raw` directory into `backend/data/raw/` and copy the metadata files into `backend/data/metadata/`. Preserve the filenames. Keep your current `backend/data/employment_data.csv` unchanged until the new loaders and API endpoints have been tested.
