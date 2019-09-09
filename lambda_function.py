import  boto3
import json
from boto3.session import Session
import os



def stack_names(stack_resp):
	existing_stack_names=[]
	for stk_name in stack_resp:
		existing_stack_names.append(stk_name['StackName'])
	return existing_stack_names




def lambda_handler(event,context):
	temp_folder = '/tmp/outputs.txt'
	accounts    = {'613454839298':'arn:aws:iam::613454839298:role/AWSCloudFormationStackSetExecutionRole','006827690841':'arn:aws:iam::006827690841:role/bala_new'} 
	sts_client  = boto3.client('sts',region_name = 'us-east-1')
	#cft_client  = boto3.client('cloudformation',region_name = 'us-east-1')
	s3_client = boto3.client('s3')
	Bucket      = 'cicd-testing-backet'
	Key         = 'bala/output.txt'
	stack_name  = 'sample-testing-stack'
	s3_client.download_file(Bucket,Key,temp_folder)
	pipeline    =  boto3.client('codepipeline')
	#print event
	with open(temp_folder) as file_name:
		data    = json.load(file_name)
		for acc_ids in data.keys():
			response = sts_client.assume_role(RoleArn = accounts[acc_ids],RoleSessionName = acc_ids,DurationSeconds = 900)
			session  = Session(aws_access_key_id = response['Credentials']['AccessKeyId'],aws_secret_access_key = response['Credentials']['SecretAccessKey'],aws_session_token = response['Credentials']['SessionToken'])
			#cft_response = session.cft_client.create_stack(StackSetName = 'sample-testing-stack',TemplateBody = 'https://'+Bucket+'s3.amazonaws.com'+str(data[acc_ids]),Parameters=[{'ParameterKey': 'AccountAlias','ParameterValue': 'tejatestingforlambda'},],Capabilities=['CAPABILITY_NAMED_IAM'])
			sess_client = session.client('cloudformation',region_name='us-east-1')
			stack_resp  = sess_client.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])['StackSummaries']
			#print stack_resp
			if stack_name not in stack_names(stack_resp): 
			    cft_response = sess_client.create_stack(StackName=stack_name,TemplateURL = 'https://'+Bucket+'.s3.amazonaws.com'+str(data[acc_ids]),Parameters=[{'ParameterKey': 'AccountAlias','ParameterValue': 'tejatestingforlambda'},],Capabilities=['CAPABILITY_NAMED_IAM'])
			    #print cft_response
			    pipe_resp=pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
			else:
			    cft_response = sess_client.update_stack(StackName = stack_name,TemplateURL = 'https://'+Bucket+'.s3.amazonaws.com'+str(data[acc_ids]),Parameters=[{'ParameterKey': 'AccountAlias','ParameterValue': 'tejatestingforlambda'},],Capabilities=['CAPABILITY_NAMED_IAM'])
			    #print cft_response
			    pipe_resp=pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])	
			    
