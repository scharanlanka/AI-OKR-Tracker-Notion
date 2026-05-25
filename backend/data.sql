--
-- PostgreSQL database dump
--

\restrict n9bsqqiy8viwz3SFCPfeWHaF5wWPbInncgXnLJAFNpSpibMZhrDYsWJaHXoPqHf

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.4 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: agent_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.agent_logs VALUES (1, 'what are the teams that fall behind', 'team_agent', 'Team summary:
- Unassigned: KRs=15, avg_progress=54%, blocked=0', '2026-05-22 00:53:54.781935');
INSERT INTO public.agent_logs VALUES (2, 'what is the status of reducing backend API latency?', 'general_agent', 'Snapshot: objectives=5, key_results=15, average_kr_progress=54%.', '2026-05-22 00:55:12.027781');
INSERT INTO public.agent_logs VALUES (3, 'which teams haven''t met 80% progress', 'team_agent', 'Team summary:
- Unassigned: KRs=15, avg_progress=54%, blocked=0', '2026-05-22 04:53:39.268619');
INSERT INTO public.agent_logs VALUES (4, 'which teams haven''t met 80% progress', 'progress_agent', 'Teams below 80% progress
- Unassigned: 54% average progress across 15 KRs', '2026-05-22 04:57:42.458711');
INSERT INTO public.agent_logs VALUES (5, 'which teams haven''t met 80% progress', 'progress_agent', 'Teams below 80% progress
- Unassigned: 54% average progress across 15 KRs', '2026-05-22 04:57:50.317194');
INSERT INTO public.agent_logs VALUES (6, 'which teams haven''t met 80% progress', 'progress_agent', 'Teams below 80% progress
- Unassigned: 54% average progress across 15 KRs', '2026-05-22 04:57:51.473868');
INSERT INTO public.agent_logs VALUES (7, 'which teams haven''t met 80% progress', 'progress_agent', 'Teams below 80% progress
- Unassigned: 54% average progress across 15 KRs', '2026-05-22 04:57:53.144668');
INSERT INTO public.agent_logs VALUES (8, 'Who is below 60% progress right now', 'progress_agent', 'Teams below 60% progress
- Unassigned: 54% average progress across 15 KRs', '2026-05-22 04:58:09.089116');
INSERT INTO public.agent_logs VALUES (9, 'Which teams haven’t met 80% progress?', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:03:10.460596');
INSERT INTO public.agent_logs VALUES (10, 'Which teams haven’t met 80% progress?', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:25:57.934506');
INSERT INTO public.agent_logs VALUES (11, 'Which teams haven’t met 80% progress?', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:26:01.500792');
INSERT INTO public.agent_logs VALUES (12, 'Which teams haven’t met 80% progress?', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:26:02.198004');
INSERT INTO public.agent_logs VALUES (13, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:26:18.196011');
INSERT INTO public.agent_logs VALUES (14, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:26:57.628247');
INSERT INTO public.agent_logs VALUES (15, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:26:58.312711');
INSERT INTO public.agent_logs VALUES (16, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:28:15.958503');
INSERT INTO public.agent_logs VALUES (17, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:28:16.987909');
INSERT INTO public.agent_logs VALUES (18, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:29:37.244763');
INSERT INTO public.agent_logs VALUES (19, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:29:37.618267');
INSERT INTO public.agent_logs VALUES (20, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:29:37.848274');
INSERT INTO public.agent_logs VALUES (21, 'which team haven''t met 80% progress', 'progress_agent', 'I could not get an LLM response for this progress query. Please check Azure LLM credentials or endpoint configuration.', '2026-05-22 05:29:38.035492');
INSERT INTO public.agent_logs VALUES (22, 'which team haven''t met 80% progress', 'progress_agent', 'The only team that hasn’t hit the 80% progress mark is:

Team Unassigned  
– Average progress: 54%  
– Number of KRs: 15', '2026-05-22 05:31:16.703726');
INSERT INTO public.agent_logs VALUES (23, 'which team haven''t met 80% progress', 'progress_agent', 'The only team that hasn’t met the 80% progress threshold is:

• Unassigned (54.0% average progress)', '2026-05-22 05:31:20.081791');
INSERT INTO public.agent_logs VALUES (24, 'which team haven''t met 80% progress', 'progress_agent', 'The only team that hasn’t reached 80% progress is:

• Unassigned – currently at 54% progress.', '2026-05-22 05:31:20.373834');
INSERT INTO public.agent_logs VALUES (25, 'which team haven''t met 80% progress', 'progress_agent', 'Here’s the team that hasn’t yet reached 80% progress:

• Unassigned – average progress 54.0% across 15 KRs', '2026-05-22 05:31:20.447359');
INSERT INTO public.agent_logs VALUES (26, 'which team haven''t met 80% progress', 'progress_agent', 'The only team that’s below 80% progress is:

• Unassigned – average progress is at 54%, well under the 80% mark.', '2026-05-22 05:31:20.804856');
INSERT INTO public.agent_logs VALUES (27, 'which team haven''t met 80% progress', 'progress_agent', 'The only team that hasn’t met the 80% progress threshold is:

• Unassigned – 54.0% average progress across 15 KRs', '2026-05-22 05:31:21.719458');
INSERT INTO public.agent_logs VALUES (28, 'what are the key results should be achieved by frontend team', 'team_agent', 'Team-level observations

• 15 key results are currently unassigned – ownership needs to be clarified  
• Average progress sits at 54% – the team is just over halfway to target  
• Zero blocked items – development flow is healthy  

Key results to drive before the next milestone

• Assign and kick off all 15 frontend KRs with clear owners  
• Push average progress from 54% to at least 80% by mid-quarter  
• Close out the remaining 46% of work so that all KRs reach 100% completion on schedule  
• Maintain zero blockages by proactively surfacing risks in daily stand-ups  ', '2026-05-22 05:32:15.1125');
INSERT INTO public.agent_logs VALUES (29, 'what are the objectives assigned to the frontend team?', 'read_agent', 'None found. There are no objectives assigned to the frontend team.', '2026-05-22 16:56:54.189031');
INSERT INTO public.agent_logs VALUES (30, 'what are the objectives assigned to the frontend team?', 'read_agent', 'There are currently no objectives assigned to the frontend team.', '2026-05-22 17:00:45.017536');
INSERT INTO public.agent_logs VALUES (31, 'what are the objectives assigned to the frontend team', 'read_agent', 'Here are the objectives assigned to the Frontend Team:

• Reduce backend API latency (In Progress)  
• Improve onboarding completion rate (Not Started)  
• Automate weekly leadership reporting (Not Started)', '2026-05-22 17:01:31.695006');
INSERT INTO public.agent_logs VALUES (32, 'which team handles Improve onboarding completion rate objective', 'read_agent', 'The “Improve onboarding completion rate” objective is handled by the Frontend Team.', '2026-05-22 17:05:31.921043');
INSERT INTO public.agent_logs VALUES (33, 'which team handles Improving onboarding completion rate objective', 'read_agent', 'The “Improve onboarding completion rate” objective is owned by the Frontend Team.', '2026-05-22 17:05:48.099495');
INSERT INTO public.agent_logs VALUES (34, 'what are the key results that are blocked due to blockers?', 'read_agent', 'None found. There are no key results flagged as blocked (i.e. with “blocked”: true) in the provided data.', '2026-05-22 17:07:53.729765');
INSERT INTO public.agent_logs VALUES (35, 'what are the key results that are blocked due to blockers?', 'read_agent', 'I don’t see any key results that are marked as blocked due to blockers.', '2026-05-22 17:23:20.518438');
INSERT INTO public.agent_logs VALUES (36, 'what are the key results that are blocked due to  API access', 'read_agent', 'None found.', '2026-05-22 17:23:55.666192');
INSERT INTO public.agent_logs VALUES (37, 'what are the key results that are blocked due to  Waiting on API access ', 'read_agent', 'None found. There are no key results blocked due to “Waiting on API access.”', '2026-05-22 17:24:14.204214');
INSERT INTO public.agent_logs VALUES (38, 'what are the key results that are blocked due to  Waiting on API access blocker', 'read_agent', 'None of the key results are currently blocked due to a “Waiting on API access” blocker.', '2026-05-22 17:24:34.249801');
INSERT INTO public.agent_logs VALUES (39, 'what are the  key results blocked due to Waiting on API access', 'read_agent', 'The following key results are blocked due to “Waiting on API access”:

• Improve AI assistant reliability – KR 1  
• Improve onboarding completion rate – KR 3', '2026-05-22 17:25:12.335926');
INSERT INTO public.agent_logs VALUES (40, 'what are the  key results under Laura', 'read_agent', 'I couldn’t find any key results owned by Laura.', '2026-05-22 17:25:54.624322');
INSERT INTO public.agent_logs VALUES (41, 'what are the  key results under Laura Johnson', 'read_agent', 'None found. There are no key results owned by Laura Johnson.', '2026-05-22 17:27:12.654244');
INSERT INTO public.agent_logs VALUES (42, 'what are the  key results owned by Laura Johnson', 'read_agent', 'None found. Laura Johnson doesn’t own any of the listed key results.', '2026-05-22 17:27:31.496424');
INSERT INTO public.agent_logs VALUES (43, 'what are the objectives owned by Laura Johnson', 'read_agent', 'None found. Laura Johnson doesn’t own any of the listed objectives.', '2026-05-22 17:28:03.545365');
INSERT INTO public.agent_logs VALUES (44, 'what are the key results owned by Laura Johnson', 'read_agent', 'No key results owned by Laura Johnson were found.', '2026-05-22 17:28:40.920577');
INSERT INTO public.agent_logs VALUES (45, 'what are the key results owned by Laura Johnson', 'read_agent', 'I’m not seeing any key results assigned to Laura Johnson.', '2026-05-22 17:28:42.658688');
INSERT INTO public.agent_logs VALUES (46, 'what are the key results owned by Laura Johnson', 'read_agent', 'Here are the three key results owned by Laura Johnson (all under the “Automate weekly leadership reporting” objective on the Frontend Team):

1. Automate weekly leadership reporting – KR 1  
   • Risk: High  
   • Status: Not Started  
   • Progress: 80%  
   • Deadline: 2026-05-22  
   • Blocked? No  

2. Automate weekly leadership reporting – KR 2  
   • Risk: High  
   • Status: Blocked  
   • Progress: 25%  
   • Deadline: 2026-05-19  
   • Blocked by: Delayed due to resource constraints  

3. Automate weekly leadership reporting – KR 3  
   • Risk: Low  
   • Status: Blocked  
   • Progress: 80%  
   • Deadline: 2026-05-19  
   • Blocked by: Dependency on design approval', '2026-05-22 17:31:50.806753');
INSERT INTO public.agent_logs VALUES (47, 'what are the key results owned by Laura', 'read_agent', 'Here are the key results owned by Laura Johnson:

• Automate weekly leadership reporting – KR 1  
• Automate weekly leadership reporting – KR 2  
• Automate weekly leadership reporting – KR 3', '2026-05-22 17:32:30.930316');
INSERT INTO public.agent_logs VALUES (48, 'what are the upcoming deadlines and their progress', 'read_agent', 'No upcoming deadlines found in the provided information.', '2026-05-22 17:36:49.299109');
INSERT INTO public.agent_logs VALUES (49, 'what are the upcoming deadlines and their progress', 'read_agent', 'None found.', '2026-05-22 17:37:22.991746');
INSERT INTO public.agent_logs VALUES (50, 'what are the upcoming deadlines and their progress', 'read_agent', 'Here are all upcoming deadlines and the current progress on each key result:

2026-05-22  
- Automate weekly leadership reporting (KR 1): 80%  
- Launch customer analytics dashboard (KR 3): 100%  

2026-05-28  
- Improve onboarding completion rate (KR 3): 10%  
- Reduce backend API latency (KR 1): 80%  

2026-06-06  
- Reduce backend API latency (KR 2): 25%  

2026-06-13  
- Improve AI assistant reliability (KR 2): 10%  

2026-06-20  
- Launch customer analytics dashboard (KR 1): 80%  

2026-06-22  
- Improve AI assistant reliability (KR 3): 80%  

2026-06-25  
- Reduce backend API latency (KR 3): 80%  

2026-06-28  
- Improve onboarding completion rate (KR 1): 45%  ', '2026-05-22 17:38:21.158772');
INSERT INTO public.agent_logs VALUES (51, 'what are the teams available', 'read_agent', 'The teams available are:
- Backend Team
- Frontend Team', '2026-05-22 17:38:53.989788');
INSERT INTO public.agent_logs VALUES (52, 'Objectives owned by Laura Johnson', 'read_agent', 'Here are the objectives owned by Laura Johnson:

• Automate weekly leadership reporting (Team: Frontend Team, Quarter: Q2, Status: Not Started)', '2026-05-22 18:59:43.342005');
INSERT INTO public.agent_logs VALUES (53, 'Show upcoming deadlines with progress', 'read_agent', 'Here are the upcoming deadlines with their current progress:

• 2026-05-22  
  – Automate weekly leadership reporting (KR 1): 80%  
  – Launch customer analytics dashboard (KR 3): 100%

• 2026-05-28  
  – Improve onboarding completion rate (KR 3): 10%  
  – Reduce backend API latency (KR 1): 80%

• 2026-06-06  
  – Reduce backend API latency (KR 2): 25%

• 2026-06-13  
  – Improve AI assistant reliability (KR 2): 10%

• 2026-06-20  
  – Launch customer analytics dashboard (KR 1): 80%

• 2026-06-22  
  – Improve AI assistant reliability (KR 3): 80%

• 2026-06-25  
  – Reduce backend API latency (KR 3): 80%

• 2026-06-28  
  – Improve onboarding completion rate (KR 1): 45%', '2026-05-22 18:59:57.993501');
INSERT INTO public.agent_logs VALUES (54, 'Objectives owned by Laura Johnson', 'read_agent', 'Here are the objectives owned by Laura Johnson:

• Automate weekly leadership reporting', '2026-05-22 19:21:27.650926');
INSERT INTO public.agent_logs VALUES (55, 'create a new objective "Enable Streaming" owned by Sai Charan Lanka by backend team in the Q2 quarter progress is not started.', 'write_agent', 'Added objective ''create a new objective "Enable Streaming" owned by Sai Charan Lanka by backend team in the Q2 quarter progress is not started.'' to Notion. Notion page id: 368cd040-39ad-81e9-a9f0-e2d88c0714a9.', '2026-05-22 19:23:17.675266');
INSERT INTO public.agent_logs VALUES (56, 'create a new objective "Enable Streaming" owned by Sai Charan Lanka by backend team in the Q2 quarter progress is not started.', 'write_agent', 'Added objective ''Enable Streaming'' to Notion (owner=Sai Charan Lanka, team=Backend Team, quarter=Q2, status=Not Started). Notion page id: 368cd040-39ad-811e-adc1-c398cee1feb6.', '2026-05-22 19:26:21.469499');
INSERT INTO public.agent_logs VALUES (57, 'can you add a key result "Improve customer retention rate - KR1", owned by Sai Charan Lanka on backend team,  with high risk,  the status is in progress due on 5th june 2026', 'write_agent', 'Added key result ''can you add a key result "Improve customer retention rate - KR1", owned by Sai Charan Lanka on backend team,  with high risk,  the status is in progress due on 5th june 2026'' to Notion. Notion page id: 368cd040-39ad-81d5-abba-e823da444545.', '2026-05-22 19:29:45.124415');
INSERT INTO public.agent_logs VALUES (58, 'can you add a key result "Improve customer retention rate - KR1", owned by Sai Charan Lanka on backend team,  with high risk,  the status is in progress due on 5th june 2026', 'write_agent', 'Added key result ''Improve customer retention rate - KR1'' to Notion (owner=Sai Charan Lanka on backend team,, team=Backend Team, risk=High, status=In Progress, due=2026-06-05). Notion page id: 368cd040-39ad-81b2-90e8-c4f6d56af946.', '2026-05-22 19:32:37.402128');
INSERT INTO public.agent_logs VALUES (59, 'can you add a key result "Improve customer retention rate - KR1", owned by Sai Charan Lanka on backend team,  with high risk,  the status is in progress due on 5th june 2026', 'write_agent', 'Added key result ''Improve customer retention rate - KR1'' to Notion (owner=Sai Charan Lanka, team=Backend Team, risk=High, status=In Progress, due=2026-06-05). Notion page id: 368cd040-39ad-81dd-877f-c3d6735ac769.', '2026-05-22 19:35:15.207316');
INSERT INTO public.agent_logs VALUES (60, 'remove can you add a key result "Improve customer retention rate - KR1", owned by Sai Charan Lanka on backend team, with high risk, the status is in progress due on 5th june 2026 key result', 'write_agent', 'Added key result ''Improve customer retention rate - KR1'' to Notion (owner=Sai Charan Lanka, team=Backend Team, risk=High, status=In Progress, due=2026-06-05). Notion page id: 368cd040-39ad-81ec-a3a1-ebbae6f7bc40.', '2026-05-22 19:36:47.451084');
INSERT INTO public.agent_logs VALUES (61, 'Which KRs are most at risk this quarter?', 'read_agent', 'Here are the Key Results this quarter marked with the highest risk (“High”):

1. Improve AI assistant reliability – KR 3  
   • Owner: Darlene Diaz (Backend Team)  
   • Status: Blocked (Dependency on design approval)

2. Improve AI assistant reliability – KR 2  
   • Owner: Darlene Diaz (Backend Team)  
   • Status: Blocked (Delayed due to resource constraints)

3. Reduce backend API latency – KR 3  
   • Owner: Belinda Rose (Frontend Team)  
   • Status: Blocked (Waiting for stakeholder review)

4. Launch customer analytics dashboard – KR 1  
   • Owner: Shelby Williamson (Backend Team)  
   • Status: Blocked (Delayed due to resource constraints)

5. Improve onboarding completion rate – KR 1  
   • Owner: Tyrone Casey (Frontend Team)  
   • Status: Blocked (Dependency on design approval)

6. Automate weekly leadership reporting – KR 1  
   • Owner: Laura Johnson (Frontend Team)  
   • Status: Not Started

7. Automate weekly leadership reporting – KR 2  
   • Owner: Laura Johnson (Frontend Team)  
   • Status: Blocked (Delayed due to resource constraints)

8. Improve customer retention rate – KR 1  
   • Owner: Sai Charan Lanka (Backend Team)  
   • Status: In Progress', '2026-05-22 19:45:50.383791');
INSERT INTO public.agent_logs VALUES (62, 'add a objective "Reduce p95 latency by caching" owned by Sai Charan Lanka on backend team, with status in progress in Q2', 'write_agent', 'Added objective ''Reduce p95 latency by caching'' to Notion (owner=Sai Charan Lanka, team=Backend Team, quarter=Q2, status=In Progress). Notion page id: 368cd040-39ad-811d-87b4-e3565a08f878.', '2026-05-22 19:53:46.386712');
INSERT INTO public.agent_logs VALUES (63, 'modify the  objective "Reduce p95 latency by caching" to "Reduce p95 latency by caching using Redis" owned by Sai Charan Lanka on backend team, with status in progress in Q2', 'write_agent', 'I can write to Notion for create/add actions. Try: ''create objective title: Improve onboarding, owner: Alice, status: On Track''.', '2026-05-22 19:56:54.359109');
INSERT INTO public.agent_logs VALUES (64, 'add a objective "Add input limit on the user side" owned by Chris Gregor on frontend team, with status in progress in Q2', 'write_agent', 'Added objective ''Add input limit on the user side'' to Notion (owner=Chris Gregor, team=Frontend Team, quarter=Q2, status=In Progress). Notion page id: 368cd040-39ad-8159-b4d5-ceea4b233515.', '2026-05-22 19:57:43.51378');


--
-- Data for Name: objectives; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.objectives VALUES (1, '367cd040-39ad-8179-91d7-d866139e7735', 'Automate weekly leadership reporting', 'Laura Johnson', 'Not Started', 0, NULL, '2026-05-22 00:53:29.008563', '2026-05-22 17:31:35.703566', 'Frontend Team', 'Q2');
INSERT INTO public.objectives VALUES (3, '367cd040-39ad-81eb-aaea-c7e3c42d10c9', 'Launch customer analytics dashboard', 'Shelby Williamson', 'Not Started', 0, NULL, '2026-05-22 00:53:29.008572', '2026-05-22 17:31:35.703574', 'Backend Team', 'Q2');
INSERT INTO public.objectives VALUES (4, '367cd040-39ad-8167-815e-c15028bf8487', 'Reduce backend API latency', 'Belinda Rose', 'In Progress', 0, NULL, '2026-05-22 00:53:29.008574', '2026-05-22 17:31:35.703575', 'Frontend Team', 'Q2');
INSERT INTO public.objectives VALUES (5, '367cd040-39ad-8188-b963-f65e2d5f8e6a', 'Improve AI assistant reliability', 'Darlene Diaz', 'In Progress', 0, NULL, '2026-05-22 00:53:29.008575', '2026-05-22 17:31:35.703576', 'Backend Team', 'Q2');
INSERT INTO public.objectives VALUES (2, '367cd040-39ad-81aa-8c40-c409012eb6b6', 'Improve onboarding completion rate', 'Tyrone Casey', 'Completed', 0, NULL, '2026-05-22 00:53:29.00857', '2026-05-22 18:57:55.727307', 'Frontend Team', 'Q2');
INSERT INTO public.objectives VALUES (7, '368cd040-39ad-811e-adc1-c398cee1feb6', 'Enable Streaming', 'Sai Charan Lanka', 'Not Started', 0, NULL, '2026-05-22 19:26:33.204607', '2026-05-22 19:26:33.204614', 'Backend Team', 'Q2');
INSERT INTO public.objectives VALUES (8, '368cd040-39ad-811d-87b4-e3565a08f878', 'Reduce p95 latency by caching', 'Sai Charan Lanka', 'In Progress', 0, NULL, '2026-05-22 19:53:53.061772', '2026-05-22 19:53:53.061785', 'Backend Team', 'Q2');
INSERT INTO public.objectives VALUES (9, '368cd040-39ad-8159-b4d5-ceea4b233515', 'Add input limit on the user side', 'Chris Gregor', 'In Progress', 0, NULL, '2026-05-22 19:57:51.711044', '2026-05-22 19:57:51.711059', 'Frontend Team', 'Q2');


--
-- Data for Name: key_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.key_results VALUES (18, '368cd040-39ad-81dd-877f-c3d6735ac769', 7, 'Improve customer retention rate - KR1', 'Sai Charan Lanka', 'In Progress', 0, '2026-06-05', false, NULL, '2026-05-22 19:35:23.92809', '2026-05-22 19:35:23.928102', 'Backend Team', 'High', NULL);
INSERT INTO public.key_results VALUES (19, '368cd040-39ad-81ec-a3a1-ebbae6f7bc40', 7, 'Improve customer retention rate - KR1', 'Sai Charan Lanka', 'In Progress', 0, '2026-06-05', false, NULL, '2026-05-22 19:36:55.216664', '2026-05-22 19:36:55.216675', 'Backend Team', 'High', NULL);
INSERT INTO public.key_results VALUES (1, '367cd040-39ad-8139-8a9c-e09d62e712fa', 1, 'Automate weekly leadership reporting - KR 3', 'Laura Johnson', 'Blocked', 0.8, '2026-05-19', true, 'Dependency on design approval', '2026-05-22 00:53:29.024682', '2026-05-22 19:45:18.445818', 'Frontend Team', 'Low', '2026-05-19');
INSERT INTO public.key_results VALUES (2, '367cd040-39ad-81b7-8ba3-cc8f070fb981', 1, 'Automate weekly leadership reporting - KR 2', 'Laura Johnson', 'Blocked', 0.25, '2026-05-19', true, 'Delayed due to resource constraints', '2026-05-22 00:53:29.024686', '2026-05-22 19:45:18.445824', 'Frontend Team', 'High', '2026-05-14');
INSERT INTO public.key_results VALUES (3, '367cd040-39ad-810f-844f-fdf2a7280a85', 1, 'Automate weekly leadership reporting - KR 1', 'Laura Johnson', 'Not Started', 0.8, '2026-05-22', false, NULL, '2026-05-22 00:53:29.024687', '2026-05-22 19:45:18.445825', 'Frontend Team', 'High', '2026-05-09');
INSERT INTO public.key_results VALUES (4, '367cd040-39ad-812d-8d0d-ce57bcc07c69', 2, 'Improve onboarding completion rate - KR 3', 'Tyrone Casey', 'Blocked', 0.1, '2026-05-28', true, 'Waiting on API access', '2026-05-22 00:53:29.024689', '2026-05-22 19:45:18.445825', 'Frontend Team', 'Medium', '2026-05-17');
INSERT INTO public.key_results VALUES (5, '367cd040-39ad-8199-9f83-d85f40a0a9e6', 2, 'Improve onboarding completion rate - KR 2', 'Tyrone Casey', 'Blocked', 0.8, '2026-05-19', true, 'Delayed due to resource constraints', '2026-05-22 00:53:29.02469', '2026-05-22 19:45:18.445826', 'Frontend Team', 'Medium', '2026-05-06');
INSERT INTO public.key_results VALUES (6, '367cd040-39ad-81aa-89c4-c3468a0fae3b', 2, 'Improve onboarding completion rate - KR 1', 'Tyrone Casey', 'Blocked', 0.45, '2026-06-28', true, 'Dependency on design approval', '2026-05-22 00:53:29.024692', '2026-05-22 19:45:18.445827', 'Frontend Team', 'High', '2026-05-17');
INSERT INTO public.key_results VALUES (7, '367cd040-39ad-817a-864a-ec0cf562562c', 3, 'Launch customer analytics dashboard - KR 3', 'Shelby Williamson', 'Blocked', 1, '2026-05-22', true, 'Waiting for stakeholder review', '2026-05-22 00:53:29.024694', '2026-05-22 19:45:18.445827', 'Backend Team', 'Delayed', '2026-05-17');
INSERT INTO public.key_results VALUES (8, '367cd040-39ad-81d4-be9d-eeba32b068a9', 3, 'Launch customer analytics dashboard - KR 2', 'Shelby Williamson', 'Blocked', 0.1, '2026-05-19', true, 'Blocked by missing test data', '2026-05-22 00:53:29.024695', '2026-05-22 19:45:18.445828', 'Backend Team', 'Low', '2026-05-19');
INSERT INTO public.key_results VALUES (9, '367cd040-39ad-81e1-adde-cba541ca1a3d', 3, 'Launch customer analytics dashboard - KR 1', 'Shelby Williamson', 'Blocked', 0.8, '2026-06-20', true, 'Delayed due to resource constraints', '2026-05-22 00:53:29.024697', '2026-05-22 19:45:18.445828', 'Backend Team', 'High', '2026-05-19');
INSERT INTO public.key_results VALUES (10, '367cd040-39ad-8186-a095-ca67b8275c54', 4, 'Reduce backend API latency - KR 3', 'Belinda Rose', 'Blocked', 0.8, '2026-06-25', true, 'Waiting for stakeholder review', '2026-05-22 00:53:29.024698', '2026-05-22 19:45:18.445829', 'Frontend Team', 'High', '2026-05-10');
INSERT INTO public.key_results VALUES (11, '367cd040-39ad-8151-a55c-e57210c8419d', 4, 'Reduce backend API latency - KR 2', 'Belinda Rose', 'Blocked', 0.25, '2026-06-06', true, 'Delayed due to resource constraints', '2026-05-22 00:53:29.0247', '2026-05-22 19:45:18.44583', 'Frontend Team', 'Low', '2026-05-15');
INSERT INTO public.key_results VALUES (12, '367cd040-39ad-810f-b890-d801e066ce6e', 4, 'Reduce backend API latency - KR 1', 'Belinda Rose', 'In Progress', 0.8, '2026-05-28', false, NULL, '2026-05-22 00:53:29.024701', '2026-05-22 19:45:18.44583', 'Frontend Team', 'Delayed', '2026-05-18');
INSERT INTO public.key_results VALUES (13, '367cd040-39ad-81c2-8b43-e6f9ee9b7f61', 5, 'Improve AI assistant reliability - KR 3', 'Darlene Diaz', 'Blocked', 0.8, '2026-06-22', true, 'Dependency on design approval', '2026-05-22 00:53:29.024703', '2026-05-22 19:45:18.445831', 'Backend Team', 'High', '2026-05-14');
INSERT INTO public.key_results VALUES (14, '367cd040-39ad-81a9-9af1-f1a66ac06a29', 5, 'Improve AI assistant reliability - KR 2', 'Darlene Diaz', 'Blocked', 0.1, '2026-06-13', true, 'Delayed due to resource constraints', '2026-05-22 00:53:29.024704', '2026-05-22 19:45:18.445831', 'Backend Team', 'High', '2026-05-14');
INSERT INTO public.key_results VALUES (15, '367cd040-39ad-81a6-ab11-cac03b7479f7', 5, 'Improve AI assistant reliability - KR 1', 'Darlene Diaz', 'Blocked', 0.25, '2026-05-20', true, 'Waiting on API access', '2026-05-22 00:53:29.024706', '2026-05-22 19:45:18.445832', 'Backend Team', 'Low', '2026-05-19');


--
-- Name: agent_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.agent_logs_id_seq', 64, true);


--
-- Name: key_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.key_results_id_seq', 19, true);


--
-- Name: objectives_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.objectives_id_seq', 9, true);


--
-- PostgreSQL database dump complete
--

\unrestrict n9bsqqiy8viwz3SFCPfeWHaF5wWPbInncgXnLJAFNpSpibMZhrDYsWJaHXoPqHf

