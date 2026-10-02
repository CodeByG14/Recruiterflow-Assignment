-- 1) List all currently open job postings, along with the name of the recruiter who owns each one.
select t1.title, t2.name
from job_postings as t1
join recruiters as t2
on t1.recruiter_id = t2.id;

 -- 2) For each job posting, how many applicants reached the Final interview stage?
select j.id, j.title, count(*) as no_of_finalist
from job_postings as j
join interviews as i
on j.id = i.job_posting_id
where stage = 'Final'
group by j.id;

-- 3) Find every person who effectively applied to more than on job posting. Careful — the data isn't as clean as it looks.
select lower(a.email) as email,
count(distinct i.job_posting_id) as postings_applied
from applicants a
join interviews i on i.applicant_id = a.id
group by lower(a.email)
having count(distinct i.job_posting_id) > 1;

-- 4) For each recruiter, compute their Final-stage conversion rate (passed ÷ total Final-stage interviews), but only include recruiters with at least 3 Final-stage interviews.
select r.id, r.name, count(*) as total_finals, count(*) filter (where i.outcome = 'passed') as total_passed, round(count(*) filter(where i.outcome = 'passed') * 1.0 / count(*),2) as conversion_rate
from recruiters as r
join job_postings as j                                               
on r.id = j.recruiter_id                                                                         
join interviews as i
on j.id = i.job_posting_id
where i.stage = 'Final'
group by r.id, r.name
having count(*) >= 3;

-- 5) (Bonus) Using a window function, find the recruiter with the most successful placements (passed at Final stage) per department.
with placements as (
    select j.department,
           r.id as recruiter_id,
           r.name,
           count(*) as placements
    from interviews i
    join job_postings j on j.id = i.job_posting_id
    join recruiters r on r.id = j.recruiter_id
    where i.stage = 'Final'
      and i.outcome = 'passed'
    group by j.department, r.id, r.name
),
ranked as (
    select *,
           rank() over (partition by department
                        order by placements desc) as rnk
    from placements
)
select department, recruiter_id, name, placements
from ranked
where rnk = 1;
