export interface Evidence { id?:string; type:string; source_url:string; excerpt:string; author:string; verification_status?:string }
export interface Experience { id:string; title:string; category:string; period:string; situation:string; task:string; action:string; result:string; lessons:string; skills:string[]; verification_status:string; is_sample:boolean; evidence:Evidence[]; created_at:string }
export interface Candidate { id:string; title:string; skills:string[]; evidence:Evidence[]; questions:string[] }
export interface Batch { batch_id:string; repository:string; is_sample:boolean; notice:string; candidates:Candidate[]; activities:Evidence[] }
export interface Source { batch:Batch; candidate:Candidate }
export interface Match { experience_id:string; title:string; related_skills:string[]; relevance_score:number; reason:string; missing_information:string[]; action:string; result:string; is_sample:boolean; verification_status:string; evidence_count:number }
export interface Application { id:string; company_name:string; job_title:string; question:string; job_description:string; character_limit:number|null; analysis:{ required_skills:string[]; required_elements:string[]; notice:string }; matches:Match[] }
export interface Draft { id:string; application_id:string; experience_id:string; content:string; character_count:number; is_sample:boolean; warnings:string[]; created_at:string; application:Application; links:{id:string;claim_text:string;evidence_id:string;verification_status:string;evidence:Evidence}[] }
export type Page = 'dashboard'|'archive'|'github'|'matching'|'drafts';
