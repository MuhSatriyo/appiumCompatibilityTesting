pipeline {

    agent any
    parameters {
        booleanParam(
            name: 'Test_DDMS',
            defaultValue: true,
            description: 'Jalankan test login untuk aplikasi DDMS (9 device Android paralel)'
        )
        booleanParam(
            name: 'Test_Prohace',
            defaultValue: true,
            description: 'Jalankan test login untuk aplikasi Prohace (9 device Android paralel)'
        )
    }

    options {
        timestamps()
        timeout(time: 60, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        BUILD_NAME           = "Jenkins ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        BROWSERSTACK_PROJECT = "Mobile Compatibility Testing"
        VENV                 = ".venv"
    }

    stages {

        stage('Validate Parameters') {
            steps {
                script {
                    if (!params.Test_DDMS && !params.Test_Prohace) {
                        error('Minimal satu parameter harus dicentang: Test_DDMS atau Test_Prohace.')
                    }
                    def suites = []
                    if (params.Test_DDMS)    suites << 'Test_DDMS'
                    if (params.Test_Prohace) suites << 'Test_Prohace'
                    echo "Suite yang akan dijalankan: ${suites.join(', ')}"
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                    set -e
                    echo "== Membersihkan artefak run sebelumnya =="
                    rm -rf results report.pdf
                    rm -f error_*.png page_source_*.xml before_username_*.png before_username_*.xml || true

                    echo "== Menyiapkan virtualenv & dependency =="
                    python3 -m venv ${VENV}
                    . ${VENV}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                withCredentials([usernamePassword(
                        credentialsId: 'browserstack-creds',
                        usernameVariable: 'BROWSERSTACK_USERNAME',
                        passwordVariable: 'BROWSERSTACK_ACCESS_KEY')]) {

                    script {
                        def parallelJobs = [:]

                        if (params.Test_DDMS) {
                            parallelJobs['DDMS Login'] = {
                                echo "[Test_DDMS] Memulai 9 device paralel..."
                                sh '''
                                    set -e
                                    . ${VENV}/bin/activate
                                    python testLoginDDMS.py
                                '''
                            }
                        }

                        if (params.Test_Prohace) {
                            parallelJobs['Prohace Login'] = {
                                echo "[Test_Prohace] Memulai 9 device paralel..."
                                sh '''
                                    set -e
                                    . ${VENV}/bin/activate
                                    python testLoginProhace.py
                                '''
                            }
                        }

                        parallel parallelJobs
                    }
                }
            }
        }

        stage('Generate PDF Report') {
            steps {
                script {
                    // Kumpulkan nama suite persis yang dipakai di hasil JSON
                    def suiteArgs = []
                    if (params.Test_DDMS)    suiteArgs << '"DDMS - Login"'
                    if (params.Test_Prohace) suiteArgs << '"Prohace - Login"'
                    def suitesFlag = suiteArgs.join(' ')

                    sh """
                        set -e
                        . ${VENV}/bin/activate
                        python generate_report.py \\
                            --results-dir results \\
                            --build-name "${BUILD_NAME}" \\
                            --suites ${suitesFlag} \\
                            --out report.pdf
                    """
                }
            }
        }

        stage('Evaluate Result') {
            steps {
                script {
                    def failed = sh(
                        script: '''grep -rl '"status": "failed"' results/ 2>/dev/null | wc -l''',
                        returnStdout: true
                    ).trim()
                    echo "Device gagal: ${failed}"
                    if (failed != "0") {
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
    }

    post {
        always {
            // Hanya simpan report.pdf sebagai artefak build
            archiveArtifacts artifacts: 'report.pdf',
                             allowEmptyArchive: true,
                             fingerprint: true
        }
        cleanup {
            // Hapus semua file sementara: venv, results JSON, screenshot, page source
            sh '''
                rm -rf ${VENV} results || true
                rm -f error_*.png page_source_*.xml before_username_*.png before_username_*.xml || true
            '''
        }
    }
}
