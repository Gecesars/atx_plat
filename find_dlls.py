import boto3

# Configurando o cliente com credenciais explícitas
s3 = boto3.client(
    's3',
    aws_access_key_id='AKIA6GBMA4WWQI5TSXG6',
    aws_secret_access_key='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',
    region_name='us-east-2'
)

def listar_arquivos_hgt(bucket_name, prefix):
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                file_name = obj['Key']
                if file_name.endswith('.hgt'):
                    print(file_name)

bucket_name = 'pastas-heroku'
prefix = 'STRM/'

listar_arquivos_hgt(bucket_name, prefix)
