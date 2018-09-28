node {
    def image
    stage('Clone repository') {
        checkout scm
    }

    stage('build image'){
    
                    image = docker.build("denbicloud/cloud-portal-client")
        }              
    stage('push image'){
    withDockerRegistry([ credentialsId: "docker1", url: "" ]) {
    image.push("dev")
   }
   }              
 }
