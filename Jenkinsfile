node {
    def image
    stage('Clone repository') {
        checkout scm
    }

    stage('build image'){
    
                    sh 'docker rmi denbicloud/cloud-portal-client'
                    image = docker.build("denbicloud/cloud-portal-client")
        }              
    stage('push image'){
    withDockerRegistry([ credentialsId: "docker1", url: "" ]) {
    image.push("dev")
   }
   }              
 }
