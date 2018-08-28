node {

    stage('Clone repository') {
        checkout scm
    }

    stage('test and publish image'){
    script {
                       withDockerRegistry([ credentialsId: "docker1", url: "" ]) {

                    def customImage = docker.build("denbicloud/cloud-portal-client")
                   customImage.inside {sh 'make test'}
                    /* Push the container to the custom Registry */
                   customImage.push("dev")
                }
}
}
}
