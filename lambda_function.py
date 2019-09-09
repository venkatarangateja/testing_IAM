import boto3
import json
from boto3.session import Session
import os


def get_stacks(sess_client):
	existing_stack_names=[]
	stack_resp  = sess_client.describe_stacks()['Stacks']
	for stk_name in stack_resp:
		existing_stack_names.append(stk_name['StackName'])
	return existing_stack_names

def init_session(accounts,acc_ids):
	sts_client  = boto3.client('sts',region_name = 'us-east-1')
	response 	= sts_client.assume_role(RoleArn = accounts[acc_ids],RoleSessionName = acc_ids,DurationSeconds = 900)
	session  	= Session(aws_access_key_id = response['Credentials']['AccessKeyId'],aws_secret_access_key = response['Credentials']['SecretAccessKey'],aws_session_token = response['Credentials']['SessionToken'])
	sess_client = session.client('cloudformation',region_name='us-east-1')
	#stack_resp  = sess_client.describe_stacks()['Stacks']
	return sess_client


def lambda_handler(event,context):
    temp_folder = '/tmp/outputs.txt'
    accounts    = {'613454839298':'arn:aws:iam::613454839298:role/AWSCloudFormationStackSetExecutionRole','006827690841':'arn:aws:iam::006827690841:role/bala_new'}
    Bucket      = 'cicd-testing-backet'
    Key         = 'bala/output.txt'
    stack_name  = 'testing-version-1'
    s3_client 	= boto3.client('s3')
    s3_client.download_file(Bucket,Key,temp_folder)
    pipeline    =  boto3.client('codepipeline')
    with open(temp_folder) as file_name:
        data  		= json.load(file_name)
        for acc_ids in data.keys():
            session_token =   init_session(accounts,acc_ids)
            stacks      = get_stacks(session_token)
            if stack_name not in get_stacks(session_token):
                try:
                    cft_response = session_token.create_stack(StackName=stack_name,TemplateURL = 'https://'+Bucket+'.s3.amazonaws.com'+str(data[acc_ids]),Parameters=[{'ParameterKey': 'AccountAlias','ParameterValue': 'tejatestingforlambda'},],Capabilities=['CAPABILITY_NAMED_IAM'])
                    print cft_response
                    pipe_resp=pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
                except Exception, e:
                    print('the error is:',e)
            else:
                try:
                    cft_response = sess_client.update_stack(StackName = stack_name,TemplateURL = 'https://'+Bucket+'.s3.amazonaws.com'+str(data[acc_ids]),Parameters=[{'ParameterKey': 'AccountAlias','ParameterValue': 'tejatestingforlambda'},],Capabilities=['CAPABILITY_NAMED_IAM'])
                    print cft_response
                    pipe_resp=pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
                except Exception, e:
                    print('The error encountered is:',e)
