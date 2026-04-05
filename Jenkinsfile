pipeline {
    agent any

    environment {
        AWS_REGION      = credentials('aws-region')
        AWS_CREDENTIALS = credentials('aws-credentials')
        PROJECT_NAME    = 'ec2-dashboard'
        GIT_REPO_URL    = 'https://github.com/SathyaProlifics/github-actions-pythonapp.git'
    }

    parameters {
        choice(name: 'ACTION', choices: ['deploy', 'destroy'], description: 'Deploy or destroy infrastructure')
        string(name: 'INSTANCE_TYPE', defaultValue: 't2.micro', description: 'EC2 instance type')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run Tests') {
            steps {
                echo '=== Running Tests ==='
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install pytest
                    pip install -r requirements.txt
                    pytest tests/ -v
                '''
            }
        }

        stage('Terraform Init') {
            steps {
                dir('terraform') {
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                     credentialsId: 'aws-credentials']]) {
                        sh '''
                            terraform init -input=false
                        '''
                    }
                }
            }
        }

        stage('Terraform Plan') {
            steps {
                dir('terraform') {
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                     credentialsId: 'aws-credentials']]) {
                        sh """
                            terraform plan \
                                -var="aws_region=${AWS_REGION}" \
                                -var="instance_type=${params.INSTANCE_TYPE}" \
                                -var="git_repo_url=${GIT_REPO_URL}" \
                                -out=tfplan \
                                -input=false
                        """
                    }
                }
            }
        }

        stage('Terraform Apply') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('terraform') {
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                     credentialsId: 'aws-credentials']]) {
                        sh '''
                            terraform apply -auto-approve -input=false tfplan
                        '''
                    }
                }
            }
        }

        stage('Terraform Destroy') {
            when {
                expression { params.ACTION == 'destroy' }
            }
            steps {
                dir('terraform') {
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                     credentialsId: 'aws-credentials']]) {
                        sh """
                            terraform destroy \
                                -var="aws_region=${AWS_REGION}" \
                                -var="instance_type=${params.INSTANCE_TYPE}" \
                                -var="git_repo_url=${GIT_REPO_URL}" \
                                -auto-approve
                        """
                    }
                }
            }
        }

        stage('Wait for Application') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('terraform') {
                    script {
                        def publicIp = sh(
                            script: 'terraform output -raw public_ip',
                            returnStdout: true
                        ).trim()

                        def appUrl = "http://${publicIp}:5000"

                        echo "=== Waiting for application at ${appUrl} ==="

                        retry(20) {
                            sleep(time: 15, unit: 'SECONDS')
                            sh "curl -f ${appUrl}/api/health"
                        }

                        echo "============================================"
                        echo " Application deployed successfully!"
                        echo " URL: ${appUrl}"
                        echo " SSH: ssh -i terraform/ec2_key.pem ec2-user@${publicIp}"
                        echo "============================================"
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
        cleanup {
            cleanWs(deleteDirs: true, patterns: [[pattern: 'venv/**', type: 'INCLUDE']])
        }
    }
}
