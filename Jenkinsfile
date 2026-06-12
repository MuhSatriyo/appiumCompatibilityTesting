pipeline {

    agent any
    options {
        timestamps()
        timeout(time: 60, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        BUILD_NAME            = "Jenkins ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        BROWSERSTACK_PROJECT  = "Mobile Compatibility Testing"
        VENV                  = ".venv"
    }

    stages {

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
                    rm -rf results report.html report.pdf
                    rm -f error_*.png page_source_*.xml before_username_*.png before_username_*.xml || true

                    echo "== Menyiapkan virtualenv & dependency =="
                    python3 -m venv ${VENV}
                    . ${VENV}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests (Parallel)') {
            steps {
                withCredentials([usernamePassword(
                        credentialsId: 'browserstack-creds',
                        usernameVariable: 'BROWSERSTACK_USERNAME',
                        passwordVariable: 'BROWSERSTACK_ACCESS_KEY')]) {

                    parallel(
                        "Prohace Login": {
                            sh '''
                                set -e
                                . ${VENV}/bin/activate
                                python testLoginProhace.py
                            '''
                        },
                        "DDMS Login": {
                            sh '''
                                set -e
                                . ${VENV}/bin/activate
                                python testLoginDDMS.py
                            '''
                        }
                    )
                }
            }
        }

        stage('Generate PDF Report') {
            steps {
                sh '''
                    set -e
                    . ${VENV}/bin/activate
                    python generate_report.py \
                        --results-dir results \
                        --build-name "${BUILD_NAME}" \
                        --html-out report.html \
                        --out report.pdf
                '''
            }
        }

        stage('Evaluate Result') {
            // Tandai build UNSTABLE bila ada device yang gagal (tanpa bikin error).
            steps {
                script {
                    def failed = sh(
                        script: '''grep -l '"status": "failed"' results/*.json 2>/dev/null | wc -l''',
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
            // Simpan PDF, HTML, JSON hasil, screenshot & page source error sebagai artefak build
            archiveArtifacts artifacts: 'report.pdf, report.html, results/*.json, error_*.png, page_source_*.xml, before_username_*.png, before_username_*.xml',
                             allowEmptyArchive: true,
                             fingerprint: true

            // Tampilkan report HTML langsung di sidebar build (butuh plugin "HTML Publisher")
            publishHTML(target: [
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'report.html',
                reportName: 'Compatibility Test Report'
            ])
        }
        cleanup {
            sh 'rm -rf ${VENV} || true'
        }
    }
}
