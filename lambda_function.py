import boto3
import json
from boto3.session import Session
import os

def get_all_stacks(sess_client):
    existing_stack_names=[]
    stack_resp  = sess_client.describe_stacks()['Stacks']
    for stk_name in stack_resp:
        existing_stack_names.append(stk_name['StackName'])
    return existing_stack_names


def get_user_params(job_data):
    
    try:
        user_parameters = job_data['actionConfiguration']['configuration']['UserParameters']
        decoded_parameters = json.loads(user_parameters)
    except Exception as e:
        raise Exception('UserParameters could not be decoded as JSON')
    
    if 'stack_name' not in decoded_parameters:
        raise Exception('Your UserParameters JSON must include the stack_name')
    
    if 'Bucket_name' not in decoded_parameters:
        raise Exception('Your UserParameters JSON must include the Bucket name')
    
    if 'Key' not in decoded_parameters:
        raise Exception('Your UserParameters JSON must include the Key name')
    
    return decoded_parameters


def init_session(accounts,acc_ids):
    sts_client  = boto3.client('sts',region_name = 'us-east-1')
    response 	= sts_client.assume_role(RoleArn = accounts[acc_ids],RoleSessionName = acc_ids,DurationSeconds = 900)
    session  	= Session(aws_access_key_id = response['Credentials']['AccessKeyId'],aws_secret_access_key = response['Credentials']['SecretAccessKey'],aws_session_token = response['Credentials']['SessionToken'])
    sess_client = session.client('cloudformation',region_name='us-east-1')
    #stack_resp  = sess_client.describe_stacks()['Stacks']
    return sess_client



def put_job_success(job_id,message):
	print('Putting job success')
    print(message)
	code_pipeline.put_job_success_result(jobId=job_id,continuationToken=job_id)


def put_job_failure(job_id,message):
    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(jobId=job_id, failureDetails={'message': message, 'type': 'JobFailed'})

def s3_client(Bucket_name,Key,):
    s3_client 	= boto3.client('s3')
    s3_client.download_file(Bucket,Key,temp_folder)

def lambda_handler(event,context):
    try:
        job_id = event['CodePipeline.job']['id']
        job_data = event['CodePipeline.job']['data']
        params = get_user_params(job_data)
        stack_name = params['stack_name']
        Bucket_name = params['Bucket_name']
        Key = params['Key']
        temp_folder = '/tmp/outputs.txt'
        s3_client(Bucket_name,Key,temp_folder)
        with open(temp_folder) as file_name:
            data  		= json.load(file_name)
            for acc_ids in data.keys():
                session_token =   init_session(accounts,acc_ids)
                stacks      = get_all_stacks(session_token)
                try:
                    if stack_name not in stacks:
                        try:
                            cft_response = session_token.create_stack(StackName=stack_name,TemplateURL = 'https://'+Bucket+'.s3.amazonaws.com'+str(data[acc_ids]),Parameters=[{'ParameterKey': 'AccountAlias','ParameterValue': 'tejatestingforlambda'},],Capabilities=['CAPABILITY_NAMED_IAM'])
                            print cft_response
                            put_job_success(job_id,'stack create complete')
                        except Exception as error:
                            print ('the stack {} in account {} already exists:'.format(stack_name,acc_ids),error)

                    else:
                        try:
                            cft_response = session_token.update_stack(StackName = stack_name,TemplateURL = 'https://'+Bucket+'.s3.amazonaws.com'+str(data[acc_ids]),Parameters=[{'ParameterKey': 'AccountAlias','ParameterValue': 'tejatestingforlambda'},],Capabilities=['CAPABILITY_NAMED_IAM'])
                            print cft_response
                            put_job_success(job_id,'stack_upadte_complete')
                        except Exception as error_1:
                            print ('the template in account {} is not updated:'.format(acc_ids),error_1)


    except Exception as error_2:
        print('Function failed due to exception.') 
        print(error_2)
        put_job_failure(job_id, 'Function exception: ' + str(error_2))
