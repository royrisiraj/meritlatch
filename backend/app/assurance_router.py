"""Authenticated engineering routes only; no arbitrary code/policy upload."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response

from .assurance_models import (CandidateCreate, CandidateChange, RunRequest, TriageRequest,
    ProposalRequest, ReviewRequest, GateRequest, CandidateRecord, RunRecord, FindingRecord,
    GateRecord, Page, Record, SuggestionState)


def build_router(service, bearer_token):
    router=APIRouter(tags=["engineering-assurance"])

    @router.post("/v1/redteam/candidates",response_model=CandidateRecord,status_code=201)
    def create(data:CandidateCreate,token:str=Depends(bearer_token)):
        return service.create_candidate(token,data.profile)

    @router.get("/v1/redteam/candidates",response_model=Page)
    def candidates(token:str=Depends(bearer_token),limit:int=Query(25,ge=1,le=50),before:str|None=Query(None,max_length=100)):
        return service.list(token,"candidates",limit,before)

    @router.get("/v1/redteam/candidates/{identifier}",response_model=CandidateRecord)
    def candidate(identifier:str,token:str=Depends(bearer_token)):
        return service.get(token,"candidate",identifier)

    @router.patch("/v1/redteam/candidates/{identifier}",response_model=CandidateRecord)
    def change(identifier:str,data:CandidateChange,token:str=Depends(bearer_token)):
        return service.change_candidate(token,identifier,data.expected_version,data.profile)

    @router.post("/v1/redteam/run",response_model=RunRecord)
    def run(data:RunRequest,response:Response,token:str=Depends(bearer_token)):
        result=service.run(token,data)
        if result["status"]=="RUNNING":response.status_code=202
        return result

    @router.get("/v1/redteam/runs",response_model=Page)
    def runs(token:str=Depends(bearer_token),limit:int=Query(25,ge=1,le=50),before:str|None=Query(None,max_length=100),candidate_id:str|None=Query(None,max_length=100)):
        return service.list(token,"runs",limit,before,{"candidate_id":candidate_id})

    @router.get("/v1/redteam/runs/{identifier}",response_model=RunRecord)
    def result(identifier:str,token:str=Depends(bearer_token)):
        return service.get(token,"run",identifier)

    @router.post("/v1/redteam/suggest",response_model=SuggestionState)
    def suggest(token:str=Depends(bearer_token)):
        return service.suggest(token)

    @router.get("/v1/alerts",response_model=Page)
    def findings(token:str=Depends(bearer_token),limit:int=Query(25,ge=1,le=50),before:str|None=Query(None,max_length=100),
        severity:Literal["HIGH","MEDIUM","LOW"]|None=None,
        status:Literal["OPEN","ACKNOWLEDGED","IN_REVIEW","DISMISSED","VERIFIED","REMEDIATION_PROPOSED"]|None=None,
        policy_id:str|None=Query(None,max_length=100)):
        return service.list(token,"findings",limit,before,{"severity":severity,"status":status,"policy_id":policy_id})

    @router.get("/v1/alerts/{identifier}",response_model=FindingRecord)
    def finding(identifier:str,token:str=Depends(bearer_token)):
        return service.get(token,"finding",identifier)

    @router.post("/v1/alerts/{identifier}/triage",response_model=FindingRecord)
    def triage(identifier:str,data:TriageRequest,token:str=Depends(bearer_token)):
        return service.triage(token,identifier,data)

    @router.post("/v1/alerts/{identifier}/remediations",response_model=Record,status_code=201)
    def propose(identifier:str,data:ProposalRequest,token:str=Depends(bearer_token)):
        return service.propose(token,identifier,data)

    @router.post("/v1/redteam/candidates/{identifier}/reviews",response_model=Record,status_code=201)
    def review(identifier:str,data:ReviewRequest,token:str=Depends(bearer_token)):
        return service.review(token,identifier,data)

    @router.post("/v1/redteam/candidates/{identifier}/release-gate",response_model=GateRecord)
    def gate(identifier:str,data:GateRequest,token:str=Depends(bearer_token)):
        return service.gate(token,identifier,data)

    @router.get("/v1/redteam/release-gates/{identifier}",response_model=GateRecord)
    def gate_result(identifier:str,token:str=Depends(bearer_token)):
        return service.get(token,"gate",identifier)

    @router.get("/v1/redteam/audit",response_model=Page)
    def audit(token:str=Depends(bearer_token),limit:int=Query(25,ge=1,le=50),before:str|None=Query(None,max_length=100),
        subject_id:str|None=Query(None,max_length=100)):
        return service.list(token,"audit",limit,before,{"subject_id":subject_id})

    return router
