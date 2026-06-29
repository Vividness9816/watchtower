Monitoring, Logging, and Debugging
Set up monitoring and logging to troubleshoot a cluster, or debug a containerized application.
Sometimes things go wrong. This guide helps you gather the relevant information and resolve issues. It has four sections:

Debugging your application - Useful for users who are deploying code into Kubernetes and wondering why it is not working.
Debugging your cluster - Useful for cluster administrators and operators troubleshooting issues with the Kubernetes cluster itself.
Logging in Kubernetes - Useful for cluster administrators who want to set up and manage logging in Kubernetes.
Monitoring in Kubernetes - Useful for cluster administrators who want to enable monitoring in a Kubernetes cluster.
You should also check the known issues for the release you're using.

Getting help
If your problem isn't answered by any of the guides above, there are variety of ways for you to get help from the Kubernetes community.

Questions
The documentation on this site has been structured to provide answers to a wide range of questions. Concepts explain the Kubernetes architecture and how each component works, while Setup provides practical instructions for getting started. Tasks show how to accomplish commonly used tasks, and Tutorials are more comprehensive walkthroughs of real-world, industry-specific, or end-to-end development scenarios. The Reference section provides detailed documentation on the Kubernetes API and command-line interfaces (CLIs), such as kubectl.

Help! My question isn't covered! I need help now!
Stack Exchange, Stack Overflow, or Server Fault
If you have questions related to software development for your containerized app, you can ask those on Stack Overflow.

If you have Kubernetes questions related to cluster management or configuration, you can ask those on Server Fault.

There are also several more specific Stack Exchange network sites which might be the right place to ask Kubernetes questions in areas such as DevOps, Software Engineering, or InfoSec.

Someone else from the community may have already asked a similar question or may be able to help with your problem.

The Kubernetes team will also monitor posts tagged Kubernetes. If there aren't any existing questions that help, please ensure that your question is on-topic on Stack Overflow, Server Fault, or the Stack Exchange Network site you're asking on, and read through the guidance on how to ask a new question, before asking a new one!

Slack
Many people from the Kubernetes community hang out on Kubernetes Slack in the #kubernetes-users channel. Slack requires registration; you can request an invitation, and registration is open to everyone). Feel free to come and ask any and all questions. Once registered, access the Kubernetes organisation in Slack via your web browser or via Slack's own dedicated app.

Once you are registered, browse the growing list of channels for various subjects of interest. For example, people new to Kubernetes may also want to join the #kubernetes-novice channel. As another example, developers should join the #kubernetes-contributors channel.

There are also many country specific / local language channels. Feel free to join these channels for localized support and info:

Country	Channels
China	#cn-users, #cn-events
Finland	#fi-users
France	#fr-users, #fr-events
Germany	#de-users, #de-events
India	#in-users, #in-events
Italy	#it-users, #it-events
Japan	#jp-users, #jp-events
Korea	#kr-users
Netherlands	#nl-users
Norway	#norw-users
Poland	#pl-users
Russia	#ru-users
Spain	#es-users
Sweden	#se-users
Turkey	#tr-users, #tr-events
Forum
You're welcome to join the official Kubernetes Forum: discuss.kubernetes.io.

Bugs and feature requests
If you have what looks like a bug, or you would like to make a feature request, please use the GitHub issue tracking system.

Before you file an issue, please search existing issues to see if your issue is already covered.

If filing a bug, please include detailed information about how to reproduce the problem, such as:

Kubernetes version: kubectl version
Cloud provider, OS distro, network configuration, and container runtime version
Steps to reproduce the problem

Debug Pods
This guide is to help users debug applications that are deployed into Kubernetes and not behaving correctly. This is not a guide for people who want to debug their cluster. For that you should check out this guide.

Diagnosing the problem
The first step in troubleshooting is triage. What is the problem? Is it your Pods, your Replication Controller or your Service?

Debugging Pods
Debugging Replication Controllers
Debugging Services
Debugging Pods
The first step in debugging a Pod is taking a look at it. Check the current state of the Pod and recent events with the following command:

kubectl describe pods ${POD_NAME}
Look at the state of the containers in the pod. Are they all Running? Have there been recent restarts?

Continue debugging depending on the state of the pods.

My pod stays pending
If a Pod is stuck in Pending it means that it can not be scheduled onto a node. Generally this is because there are insufficient resources of one type or another that prevent scheduling. Look at the output of the kubectl describe ... command above. There should be messages from the scheduler about why it can not schedule your pod. Reasons include:

You don't have enough resources: You may have exhausted the supply of CPU or Memory in your cluster, in this case you need to delete Pods, adjust resource requests, or add new nodes to your cluster. See Compute Resources document for more information.

You are using hostPort: When you bind a Pod to a hostPort there are a limited number of places that pod can be scheduled. In most cases, hostPort is unnecessary, try using a Service object to expose your Pod. If you do require hostPort then you can only schedule as many Pods as there are nodes in your Kubernetes cluster.

My pod stays waiting
If a Pod is stuck in the Waiting state, then it has been scheduled to a worker node, but it can't run on that machine. Again, the information from kubectl describe ... should be informative. The most common cause of Waiting pods is a failure to pull the image. There are three things to check:

Make sure that you have the name of the image correct.
Have you pushed the image to the registry?
Try to manually pull the image to see if the image can be pulled. For example, if you use Docker on your PC, run docker pull <image>.
My pod stays terminating
If a Pod is stuck in the Terminating state, it means that a deletion has been issued for the Pod, but the control plane is unable to delete the Pod object.

This typically happens if the Pod has a finalizer and there is an admission webhook installed in the cluster that prevents the control plane from removing the finalizer.

To identify this scenario, check if your cluster has any ValidatingWebhookConfiguration or MutatingWebhookConfiguration that target UPDATE operations for pods resources.

If the webhook is provided by a third-party:

Make sure you are using the latest version.
Disable the webhook for UPDATE operations.
Report an issue with the corresponding provider.
If you are the author of the webhook:

For a mutating webhook, make sure it never changes immutable fields on UPDATE operations. For example, changes to containers are usually not allowed.
For a validating webhook, make sure that your validation policies only apply to new changes. In other words, you should allow Pods with existing violations to pass validation. This allows Pods that were created before the validating webhook was installed to continue running.
My pod is crashing or otherwise unhealthy
Once your pod has been scheduled, the methods described in Debug Running Pods are available for debugging.

My pod is running but not doing what I told it to do
If your pod is not behaving as you expected, it may be that there was an error in your pod description (e.g. mypod.yaml file on your local machine), and that the error was silently ignored when you created the pod. Often a section of the pod description is nested incorrectly, or a key name is typed incorrectly, and so the key is ignored. For example, if you misspelled command as commnd then the pod will be created but will not use the command line you intended it to use.

The first thing to do is to delete your pod and try creating it again with the --validate option. For example, run kubectl apply --validate -f mypod.yaml. If you misspelled command as commnd then will give an error like this:

I0805 10:43:25.129850   46757 schema.go:126] unknown field: commnd
I0805 10:43:25.129973   46757 schema.go:129] this may be a false alarm, see https://github.com/kubernetes/kubernetes/issues/6842
pods/mypod
The next thing to check is whether the pod on the apiserver matches the pod you meant to create (e.g. in a yaml file on your local machine). For example, run kubectl get pods/mypod -o yaml > mypod-on-apiserver.yaml and then manually compare the original pod description, mypod.yaml with the one you got back from apiserver, mypod-on-apiserver.yaml. There will typically be some lines on the "apiserver" version that are not on the original version. This is expected. However, if there are lines on the original that are not on the apiserver version, then this may indicate a problem with your pod spec.

Debugging Replication Controllers
Replication controllers are fairly straightforward. They can either create Pods or they can't. If they can't create pods, then please refer to the instructions above to debug your pods.

You can also use kubectl describe rc ${CONTROLLER_NAME} to introspect events related to the replication controller.

Debugging Services
Services provide load balancing across a set of pods. There are several common problems that can make Services not work properly. The following instructions should help debug Service problems.

First, verify that there are endpoints for the service. For every Service object, the apiserver makes one or more EndpointSlice resources available.

You can view these resources with:

kubectl get endpointslices -l kubernetes.io/service-name=${SERVICE_NAME}
Make sure that the endpoints in the EndpointSlices match up with the number of pods that you expect to be members of your service. For example, if your Service is for an nginx container with 3 replicas, you would expect to see three different IP addresses in the Service's endpoint slices.

My service is missing endpoints
If you are missing endpoints, try listing pods using the labels that Service uses. Imagine that you have a Service where the labels are:

...
spec:
  - selector:
     name: nginx
     type: frontend
You can use:

kubectl get pods --selector=name=nginx,type=frontend
to list pods that match this selector. Verify that the list matches the Pods that you expect to provide your Service. Verify that the pod's containerPort matches up with the Service's targetPort

Network traffic is not forwarded
Please see debugging service for more information.

What's next
If none of the above solves your problem, follow the instructions in Debugging Service document to make sure that your Service is running, has Endpoints, and your Pods are actually serving; you have DNS working, iptables rules installed, and kube-proxy does not seem to be misbehaving.

You may also visit troubleshooting document for more information

Debug Services
An issue that comes up rather frequently for new installations of Kubernetes is that a Service is not working properly. You've run your Pods through a Deployment (or other workload controller) and created a Service, but you get no response when you try to access it. This document will hopefully help you to figure out what's going wrong.

Running commands in a Pod
For many steps here you will want to see what a Pod running in the cluster sees. The simplest way to do this is to run an interactive busybox Pod:

kubectl run -it --rm --restart=Never busybox --image=registry.k8s.io/busybox:1.27.2 sh
Note:
If you don't see a command prompt, try pressing enter.
If you already have a running Pod that you prefer to use, you can run a command in it using:

kubectl exec <POD-NAME> -c <CONTAINER-NAME> -- <COMMAND>
Setup
For the purposes of this walk-through, let's run some Pods. Since you're probably debugging your own Service you can substitute your own details, or you can follow along and get a second data point.

kubectl create deployment hostnames --image=registry.k8s.io/serve_hostname
deployment.apps/hostnames created
kubectl commands will print the type and name of the resource created or mutated, which can then be used in subsequent commands.

Let's scale the deployment to 3 replicas.

kubectl scale deployment hostnames --replicas=3
deployment.apps/hostnames scaled
Note that this is the same as if you had started the Deployment with the following YAML:

apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: hostnames
  name: hostnames
spec:
  selector:
    matchLabels:
      app: hostnames
  replicas: 3
  template:
    metadata:
      labels:
        app: hostnames
    spec:
      containers:
      - name: hostnames
        image: registry.k8s.io/serve_hostname
The label "app" is automatically set by kubectl create deployment to the name of the Deployment.

You can confirm your Pods are running:

kubectl get pods -l app=hostnames
NAME                        READY     STATUS    RESTARTS   AGE
hostnames-632524106-bbpiw   1/1       Running   0          2m
hostnames-632524106-ly40y   1/1       Running   0          2m
hostnames-632524106-tlaok   1/1       Running   0          2m
You can also confirm that your Pods are serving. You can get the list of Pod IP addresses and test them directly.

kubectl get pods -l app=hostnames \
    -o go-template='{{range .items}}{{.status.podIP}}{{"\n"}}{{end}}'
10.244.0.5
10.244.0.6
10.244.0.7
The example container used for this walk-through serves its own hostname via HTTP on port 9376, but if you are debugging your own app, you'll want to use whatever port number your Pods are listening on.

From within a pod:

for ep in 10.244.0.5:9376 10.244.0.6:9376 10.244.0.7:9376; do
    wget -qO- $ep
done
This should produce something like:

hostnames-632524106-bbpiw
hostnames-632524106-ly40y
hostnames-632524106-tlaok
If you are not getting the responses you expect at this point, your Pods might not be healthy or might not be listening on the port you think they are. You might find kubectl logs to be useful for seeing what is happening, or perhaps you need to kubectl exec directly into your Pods and debug from there.

Assuming everything has gone to plan so far, you can start to investigate why your Service doesn't work.

Does the Service exist?
The astute reader will have noticed that you did not actually create a Service yet - that is intentional. This is a step that sometimes gets forgotten, and is the first thing to check.

What would happen if you tried to access a non-existent Service? If you have another Pod that consumes this Service by name you would get something like:

wget -O- hostnames
Resolving hostnames (hostnames)... failed: Name or service not known.
wget: unable to resolve host address 'hostnames'
The first thing to check is whether that Service actually exists:

kubectl get svc hostnames
No resources found.
Error from server (NotFound): services "hostnames" not found
Let's create the Service. As before, this is for the walk-through - you can use your own Service's details here.

kubectl expose deployment hostnames --port=80 --target-port=9376
service/hostnames exposed
And read it back:

kubectl get svc hostnames
NAME        TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
hostnames   ClusterIP   10.0.1.175   <none>        80/TCP    5s
Now you know that the Service exists.

As before, this is the same as if you had started the Service with YAML:

apiVersion: v1
kind: Service
metadata:
  labels:
    app: hostnames
  name: hostnames
spec:
  selector:
    app: hostnames
  ports:
  - name: default
    protocol: TCP
    port: 80
    targetPort: 9376
In order to highlight the full range of configuration, the Service you created here uses a different port number than the Pods. For many real-world Services, these values might be the same.

Any Network Policy Ingress rules affecting the target Pods?
If you have deployed any Network Policy Ingress rules which may affect incoming traffic to hostnames-* Pods, these need to be reviewed.

Please refer to Network Policies for more details.

Does the Service work by DNS name?
One of the most common ways that clients consume a Service is through a DNS name.

From a Pod in the same Namespace:

nslookup hostnames
Address 1: 10.0.0.10 kube-dns.kube-system.svc.cluster.local

Name:      hostnames
Address 1: 10.0.1.175 hostnames.default.svc.cluster.local
If this fails, perhaps your Pod and Service are in different Namespaces, try a namespace-qualified name (again, from within a Pod):

nslookup hostnames.default
Address 1: 10.0.0.10 kube-dns.kube-system.svc.cluster.local

Name:      hostnames.default
Address 1: 10.0.1.175 hostnames.default.svc.cluster.local
If this works, you'll need to adjust your app to use a cross-namespace name, or run your app and Service in the same Namespace. If this still fails, try a fully-qualified name:

nslookup hostnames.default.svc.cluster.local
Address 1: 10.0.0.10 kube-dns.kube-system.svc.cluster.local

Name:      hostnames.default.svc.cluster.local
Address 1: 10.0.1.175 hostnames.default.svc.cluster.local
Note the suffix here: "default.svc.cluster.local". The "default" is the Namespace you're operating in. The "svc" denotes that this is a Service. The "cluster.local" is your cluster domain, which COULD be different in your own cluster.

You can also try this from a Node in the cluster:

Note:
10.0.0.10 is the cluster's DNS Service IP, yours might be different.
nslookup hostnames.default.svc.cluster.local 10.0.0.10
Server:         10.0.0.10
Address:        10.0.0.10#53

Name:   hostnames.default.svc.cluster.local
Address: 10.0.1.175
If you are able to do a fully-qualified name lookup but not a relative one, you need to check that your /etc/resolv.conf file in your Pod is correct. From within a Pod:

cat /etc/resolv.conf
You should see something like:

nameserver 10.0.0.10
search default.svc.cluster.local svc.cluster.local cluster.local example.com
options ndots:5
The nameserver line must indicate your cluster's DNS Service. This is passed into kubelet with the --cluster-dns flag.

The search line must include an appropriate suffix for you to find the Service name. In this case it is looking for Services in the local Namespace ("default.svc.cluster.local"), Services in all Namespaces ("svc.cluster.local"), and lastly for names in the cluster ("cluster.local"). Depending on your own install you might have additional records after that (up to 6 total). The cluster suffix is passed into kubelet with the --cluster-domain flag. Throughout this document, the cluster suffix is assumed to be "cluster.local". Your own clusters might be configured differently, in which case you should change that in all of the previous commands.

The options line must set ndots high enough that your DNS client library considers search paths at all. Kubernetes sets this to 5 by default, which is high enough to cover all of the DNS names it generates.

Does any Service work by DNS name?
If the above still fails, DNS lookups are not working for your Service. You can take a step back and see what else is not working. The Kubernetes master Service should always work. From within a Pod:

nslookup kubernetes.default
Server:    10.0.0.10
Address 1: 10.0.0.10 kube-dns.kube-system.svc.cluster.local

Name:      kubernetes.default
Address 1: 10.0.0.1 kubernetes.default.svc.cluster.local
If this fails, please see the kube-proxy section of this document, or even go back to the top of this document and start over, but instead of debugging your own Service, debug the DNS Service.

Does the Service work by IP?
Assuming you have confirmed that DNS works, the next thing to test is whether your Service works by its IP address. From a Pod in your cluster, access the Service's IP (from kubectl get above).

for i in $(seq 1 3); do 
    wget -qO- 10.0.1.175:80
done
This should produce something like:

hostnames-632524106-bbpiw
hostnames-632524106-ly40y
hostnames-632524106-tlaok
If your Service is working, you should get correct responses. If not, there are a number of things that could be going wrong. Read on.

Is the Service defined correctly?
It might sound silly, but you should really double and triple check that your Service is correct and matches your Pod's port. Read back your Service and verify it:

kubectl get service hostnames -o json
{
    "kind": "Service",
    "apiVersion": "v1",
    "metadata": {
        "name": "hostnames",
        "namespace": "default",
        "uid": "428c8b6c-24bc-11e5-936d-42010af0a9bc",
        "resourceVersion": "347189",
        "creationTimestamp": "2015-07-07T15:24:29Z",
        "labels": {
            "app": "hostnames"
        }
    },
    "spec": {
        "ports": [
            {
                "name": "default",
                "protocol": "TCP",
                "port": 80,
                "targetPort": 9376,
                "nodePort": 0
            }
        ],
        "selector": {
            "app": "hostnames"
        },
        "clusterIP": "10.0.1.175",
        "type": "ClusterIP",
        "sessionAffinity": "None"
    },
    "status": {
        "loadBalancer": {}
    }
}
Is the Service port you are trying to access listed in spec.ports[]?
Is the targetPort correct for your Pods (some Pods use a different port than the Service)?
If you meant to use a numeric port, is it a number (9376) or a string "9376"?
If you meant to use a named port, do your Pods expose a port with the same name?
Is the port's protocol correct for your Pods?
Does the Service have any EndpointSlices?
If you got this far, you have confirmed that your Service is correctly defined and is resolved by DNS. Now let's check that the Pods you ran are actually being selected by the Service.

Earlier you saw that the Pods were running. You can re-check that:

kubectl get pods -l app=hostnames
NAME                        READY     STATUS    RESTARTS   AGE
hostnames-632524106-bbpiw   1/1       Running   0          1h
hostnames-632524106-ly40y   1/1       Running   0          1h
hostnames-632524106-tlaok   1/1       Running   0          1h
The -l app=hostnames argument is a label selector configured on the Service.

The "AGE" column says that these Pods are about an hour old, which implies that they are running fine and not crashing.

The "RESTARTS" column says that these pods are not crashing frequently or being restarted. Frequent restarts could lead to intermittent connectivity issues. If the restart count is high, read more about how to debug pods.

Inside the Kubernetes system is a control loop which evaluates the selector of every Service and saves the results into one or more EndpointSlice objects.

kubectl get endpointslices -l kubernetes.io/service-name=hostnames

NAME              ADDRESSTYPE   PORTS   ENDPOINTS
hostnames-ytpni   IPv4          9376    10.244.0.5,10.244.0.6,10.244.0.7
This confirms that the EndpointSlice controller has found the correct Pods for your Service. If the ENDPOINTS column is <none>, you should check that the spec.selector field of your Service actually selects for metadata.labels values on your Pods. A common mistake is to have a typo or other error, such as the Service selecting for app=hostnames, but the Deployment specifying run=hostnames, as in versions previous to 1.18, where the kubectl run command could have been also used to create a Deployment.

Are the Pods working?
At this point, you know that your Service exists and has selected your Pods. At the beginning of this walk-through, you verified the Pods themselves. Let's check again that the Pods are actually working - you can bypass the Service mechanism and go straight to the Pods, as listed by the Endpoints above.

Note:
These commands use the Pod port (9376), rather than the Service port (80).
From within a Pod:

for ep in 10.244.0.5:9376 10.244.0.6:9376 10.244.0.7:9376; do
    wget -qO- $ep
done
This should produce something like:

hostnames-632524106-bbpiw
hostnames-632524106-ly40y
hostnames-632524106-tlaok
You expect each Pod in the endpoints list to return its own hostname. If this is not what happens (or whatever the correct behavior is for your own Pods), you should investigate what's happening there.

Is the kube-proxy working?
If you get here, your Service is running, has EndpointSlices, and your Pods are actually serving. At this point, the whole Service proxy mechanism is suspect. Let's confirm it, piece by piece.

The default implementation of Services, and the one used on most clusters, is kube-proxy. This is a program that runs on every node and configures one of a small set of mechanisms for providing the Service abstraction. If your cluster does not use kube-proxy, the following sections will not apply, and you will have to investigate whatever implementation of Services you are using.

Is kube-proxy running?
Confirm that kube-proxy is running on your Nodes. Running directly on a Node, you should get something like the below:

ps auxw | grep kube-proxy
root  4194  0.4  0.1 101864 17696 ?    Sl Jul04  25:43 /usr/local/bin/kube-proxy --master=https://kubernetes-master --kubeconfig=/var/lib/kube-proxy/kubeconfig --v=2
Next, confirm that it is not failing something obvious, like contacting the master. To do this, you'll have to look at the logs. Accessing the logs depends on your Node OS. On some OSes it is a file, such as /var/log/kube-proxy.log, while other OSes use journalctl to access logs. You should see something like:

I1027 22:14:53.995134    5063 server.go:200] Running in resource-only container "/kube-proxy"
I1027 22:14:53.998163    5063 server.go:247] Using iptables Proxier.
I1027 22:14:54.038140    5063 proxier.go:352] Setting endpoints for "kube-system/kube-dns:dns-tcp" to [10.244.1.3:53]
I1027 22:14:54.038164    5063 proxier.go:352] Setting endpoints for "kube-system/kube-dns:dns" to [10.244.1.3:53]
I1027 22:14:54.038209    5063 proxier.go:352] Setting endpoints for "default/kubernetes:https" to [10.240.0.2:443]
I1027 22:14:54.038238    5063 proxier.go:429] Not syncing iptables until Services and Endpoints have been received from master
I1027 22:14:54.040048    5063 proxier.go:294] Adding new service "default/kubernetes:https" at 10.0.0.1:443/TCP
I1027 22:14:54.040154    5063 proxier.go:294] Adding new service "kube-system/kube-dns:dns" at 10.0.0.10:53/UDP
I1027 22:14:54.040223    5063 proxier.go:294] Adding new service "kube-system/kube-dns:dns-tcp" at 10.0.0.10:53/TCP
If you see error messages about not being able to contact the master, you should double-check your Node configuration and installation steps.

Kube-proxy can run in one of a few modes. In the log listed above, the line Using iptables Proxier indicates that kube-proxy is running in "iptables" mode. The most common other mode is "ipvs".

Iptables mode
In "iptables" mode, you should see something like the following on a Node:

iptables-save | grep hostnames
-A KUBE-SEP-57KPRZ3JQVENLNBR -s 10.244.3.6/32 -m comment --comment "default/hostnames:" -j MARK --set-xmark 0x00004000/0x00004000
-A KUBE-SEP-57KPRZ3JQVENLNBR -p tcp -m comment --comment "default/hostnames:" -m tcp -j DNAT --to-destination 10.244.3.6:9376
-A KUBE-SEP-WNBA2IHDGP2BOBGZ -s 10.244.1.7/32 -m comment --comment "default/hostnames:" -j MARK --set-xmark 0x00004000/0x00004000
-A KUBE-SEP-WNBA2IHDGP2BOBGZ -p tcp -m comment --comment "default/hostnames:" -m tcp -j DNAT --to-destination 10.244.1.7:9376
-A KUBE-SEP-X3P2623AGDH6CDF3 -s 10.244.2.3/32 -m comment --comment "default/hostnames:" -j MARK --set-xmark 0x00004000/0x00004000
-A KUBE-SEP-X3P2623AGDH6CDF3 -p tcp -m comment --comment "default/hostnames:" -m tcp -j DNAT --to-destination 10.244.2.3:9376
-A KUBE-SERVICES -d 10.0.1.175/32 -p tcp -m comment --comment "default/hostnames: cluster IP" -m tcp --dport 80 -j KUBE-SVC-NWV5X2332I4OT4T3
-A KUBE-SVC-NWV5X2332I4OT4T3 -m comment --comment "default/hostnames:" -m statistic --mode random --probability 0.33332999982 -j KUBE-SEP-WNBA2IHDGP2BOBGZ
-A KUBE-SVC-NWV5X2332I4OT4T3 -m comment --comment "default/hostnames:" -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-X3P2623AGDH6CDF3
-A KUBE-SVC-NWV5X2332I4OT4T3 -m comment --comment "default/hostnames:" -j KUBE-SEP-57KPRZ3JQVENLNBR
For each port of each Service, there should be 1 rule in KUBE-SERVICES and one KUBE-SVC-<hash> chain. For each Pod endpoint, there should be a small number of rules in that KUBE-SVC-<hash> and one KUBE-SEP-<hash> chain with a small number of rules in it. The exact rules will vary based on your exact config (including node-ports and load-balancers).

IPVS mode
In "ipvs" mode, you should see something like the following on a Node:

ipvsadm -ln
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
...
TCP  10.0.1.175:80 rr
  -> 10.244.0.5:9376               Masq    1      0          0
  -> 10.244.0.6:9376               Masq    1      0          0
  -> 10.244.0.7:9376               Masq    1      0          0
...
For each port of each Service, plus any NodePorts, external IPs, and load-balancer IPs, kube-proxy will create a virtual server. For each Pod endpoint, it will create corresponding real servers. In this example, service hostnames(10.0.1.175:80) has 3 endpoints(10.244.0.5:9376, 10.244.0.6:9376, 10.244.0.7:9376).

Is kube-proxy proxying?
Assuming you do see one the above cases, try again to access your Service by IP from one of your Nodes:

curl 10.0.1.175:80
hostnames-632524106-bbpiw
If this still fails, look at the kube-proxy logs for specific lines like:

Setting endpoints for default/hostnames:default to [10.244.0.5:9376 10.244.0.6:9376 10.244.0.7:9376]
If you don't see those, try restarting kube-proxy with the -v flag set to 4, and then look at the logs again.

Edge case: A Pod fails to reach itself via the Service IP
This might sound unlikely, but it does happen and it is supposed to work.

This can happen when the network is not properly configured for "hairpin" traffic, usually when kube-proxy is running in iptables mode and Pods are connected with bridge network. The Kubelet exposes a hairpin-mode flag that allows endpoints of a Service to loadbalance back to themselves if they try to access their own Service VIP. The hairpin-mode flag must either be set to hairpin-veth or promiscuous-bridge.

The common steps to trouble shoot this are as follows:

Confirm hairpin-mode is set to hairpin-veth or promiscuous-bridge. You should see something like the below. hairpin-mode is set to promiscuous-bridge in the following example.
ps auxw | grep kubelet
root      3392  1.1  0.8 186804 65208 ?        Sl   00:51  11:11 /usr/local/bin/kubelet --enable-debugging-handlers=true --config=/etc/kubernetes/manifests --allow-privileged=True --v=4 --cluster-dns=10.0.0.10 --cluster-domain=cluster.local --configure-cbr0=true --cgroup-root=/ --system-cgroups=/system --hairpin-mode=promiscuous-bridge --runtime-cgroups=/docker-daemon --kubelet-cgroups=/kubelet --babysit-daemons=true --max-pods=110 --serialize-image-pulls=false --outofdisk-transition-frequency=0
Confirm the effective hairpin-mode. To do this, you'll have to look at kubelet log. Accessing the logs depends on your Node OS. On some OSes it is a file, such as /var/log/kubelet.log, while other OSes use journalctl to access logs. Please be noted that the effective hairpin mode may not match --hairpin-mode flag due to compatibility. Check if there is any log lines with key word hairpin in kubelet.log. There should be log lines indicating the effective hairpin mode, like something below.
I0629 00:51:43.648698    3252 kubelet.go:380] Hairpin mode set to "promiscuous-bridge"
If the effective hairpin mode is hairpin-veth, ensure the Kubelet has the permission to operate in /sys on node. If everything works properly, you should see something like:
for intf in /sys/devices/virtual/net/cbr0/brif/*; do cat $intf/hairpin_mode; done
1
1
1
1
If the effective hairpin mode is promiscuous-bridge, ensure Kubelet has the permission to manipulate linux bridge on node. If cbr0 bridge is used and configured properly, you should see:
ifconfig cbr0 |grep PROMISC
UP BROADCAST RUNNING PROMISC MULTICAST  MTU:1460  Metric:1
Seek help if none of above works out.

Debug a StatefulSet
This task shows you how to debug a StatefulSet.

Before you begin
You need to have a Kubernetes cluster, and the kubectl command-line tool must be configured to communicate with your cluster.
You should have a StatefulSet running that you want to investigate.
Debugging a StatefulSet
In order to list all the pods which belong to a StatefulSet, which have a label app.kubernetes.io/name=MyApp set on them, you can use the following:

kubectl get pods -l app.kubernetes.io/name=MyApp
If you find that any Pods listed are in Unknown or Terminating state for an extended period of time, refer to the Deleting StatefulSet Pods task for instructions on how to deal with them. You can debug individual Pods in a StatefulSet using the Debugging Pods guide.

Determine the Reason for Pod Failure
This page shows how to write and read a Container termination message.

Termination messages provide a way for containers to write information about fatal events to a location where it can be easily retrieved and surfaced by tools like dashboards and monitoring software. In most cases, information that you put in a termination message should also be written to the general Kubernetes logs.

Before you begin
You need to have a Kubernetes cluster, and the kubectl command-line tool must be configured to communicate with your cluster. It is recommended to run this tutorial on a cluster with at least two nodes that are not acting as control plane hosts. If you do not already have a cluster, you can create one by using minikube or you can use one of these Kubernetes playgrounds:

iximiuz Labs
Killercoda
KodeKloud
Writing and reading a termination message
In this exercise, you create a Pod that runs one container. The manifest for that Pod specifies a command that runs when the container starts:

debug/termination.yaml
Copy debug/termination.yaml to clipboard
apiVersion: v1
kind: Pod
metadata:
  name: termination-demo
spec:
  containers:
  - name: termination-demo-container
    image: debian
    command: ["/bin/sh"]
    args: ["-c", "sleep 10 && echo Sleep expired > /dev/termination-log"]
Create a Pod based on the YAML configuration file:

kubectl apply -f https://k8s.io/examples/debug/termination.yaml
In the YAML file, in the command and args fields, you can see that the container sleeps for 10 seconds and then writes "Sleep expired" to the /dev/termination-log file. After the container writes the "Sleep expired" message, it terminates.

Display information about the Pod:

kubectl get pod termination-demo
Repeat the preceding command until the Pod is no longer running.

Display detailed information about the Pod:

kubectl get pod termination-demo --output=yaml
The output includes the "Sleep expired" message:

apiVersion: v1
kind: Pod
...
    lastState:
      terminated:
        containerID: ...
        exitCode: 0
        finishedAt: ...
        message: |
          Sleep expired
        ...
Use a Go template to filter the output so that it includes only the termination message:

kubectl get pod termination-demo -o go-template="{{range .status.containerStatuses}}{{.lastState.terminated.message}}{{end}}"
If you are running a multi-container Pod, you can use a Go template to include the container's name. By doing so, you can discover which of the containers is failing:

kubectl get pod multi-container-pod -o go-template='{{range .status.containerStatuses}}{{printf "%s:\n%s\n\n" .name .lastState.terminated.message}}{{end}}'
Customizing the termination message
Kubernetes retrieves termination messages from the termination message file specified in the terminationMessagePath field of a Container, which has a default value of /dev/termination-log. By customizing this field, you can tell Kubernetes to use a different file. Kubernetes use the contents from the specified file to populate the Container's status message on both success and failure.

The termination message is intended to be brief final status, such as an assertion failure message. The kubelet truncates messages that are longer than 4096 bytes.

The total message length across all containers is limited to 12KiB, divided equally among each container. For example, if there are 12 containers (initContainers or containers), each has 1024 bytes of available termination message space.

The default termination message path is /dev/termination-log. You cannot set the termination message path after a Pod is launched.

In the following example, the container writes termination messages to /tmp/my-log for Kubernetes to retrieve:

apiVersion: v1
kind: Pod
metadata:
  name: msg-path-demo
spec:
  containers:
  - name: msg-path-demo-container
    image: debian
    terminationMessagePath: "/tmp/my-log"
Moreover, users can set the terminationMessagePolicy field of a Container for further customization. This field defaults to "File" which means the termination messages are retrieved only from the termination message file. By setting the terminationMessagePolicy to "FallbackToLogsOnError", you can tell Kubernetes to use the last chunk of container log output if the termination message file is empty and the container exited with an error. The log output is limited to 2048 bytes or 80 lines, whichever is smaller.

Debug Init Containers
This page shows how to investigate problems related to the execution of Init Containers. The example command lines below refer to the Pod as <pod-name> and the Init Containers as <init-container-1> and <init-container-2>.

Before you begin
You need to have a Kubernetes cluster, and the kubectl command-line tool must be configured to communicate with your cluster. It is recommended to run this tutorial on a cluster with at least two nodes that are not acting as control plane hosts. If you do not already have a cluster, you can create one by using minikube or you can use one of these Kubernetes playgrounds:

iximiuz Labs
Killercoda
KodeKloud
To check the version, enter kubectl version.

You should be familiar with the basics of Init Containers.
You should have Configured an Init Container.
Checking the status of Init Containers
Display the status of your pod:

kubectl get pod <pod-name>
For example, a status of Init:1/2 indicates that one of two Init Containers has completed successfully:

NAME         READY     STATUS     RESTARTS   AGE
<pod-name>   0/1       Init:1/2   0          7s
See Understanding Pod status for more examples of status values and their meanings.

Getting details about Init Containers
View more detailed information about Init Container execution:

kubectl describe pod <pod-name>
For example, a Pod with two Init Containers might show the following:

Init Containers:
  <init-container-1>:
    Container ID:    ...
    ...
    State:           Terminated
      Reason:        Completed
      Exit Code:     0
      Started:       ...
      Finished:      ...
    Ready:           True
    Restart Count:   0
    ...
  <init-container-2>:
    Container ID:    ...
    ...
    State:           Waiting
      Reason:        CrashLoopBackOff
    Last State:      Terminated
      Reason:        Error
      Exit Code:     1
      Started:       ...
      Finished:      ...
    Ready:           False
    Restart Count:   3
    ...
You can also access the Init Container statuses programmatically by reading the status.initContainerStatuses field on the Pod Spec:

kubectl get pod <pod-name> --template '{{.status.initContainerStatuses}}'
This command will return the same information as above, formatted using a Go template.

Accessing logs from Init Containers
Pass the Init Container name along with the Pod name to access its logs.

kubectl logs <pod-name> -c <init-container-2>
Init Containers that run a shell script print commands as they're executed. For example, you can do this in Bash by running set -x at the beginning of the script.

Understanding Pod status
A Pod status beginning with Init: summarizes the status of Init Container execution. The table below describes some example status values that you might see while debugging Init Containers.

Status	Meaning
Init:N/M	The Pod has M Init Containers, and N have completed so far.
Init:Error	An Init Container has failed to execute.
Init:CrashLoopBackOff	An Init Container has failed repeatedly.
Pending	The Pod has not yet begun executing Init Containers.
PodInitializing or Running	The Pod has already finished executing Init Containers.
Debug Running Pods
This page explains how to debug Pods running (or crashing) on a Node.

Before you begin
Your Pod should already be scheduled and running. If your Pod is not yet running, start with Debugging Pods.
For some of the advanced debugging steps you need to know on which Node the Pod is running and have shell access to run commands on that Node. You don't need that access to run the standard debug steps that use kubectl.
Using kubectl describe pod to fetch details about pods
For this example we'll use a Deployment to create two pods, similar to the earlier example.

application/nginx-with-request.yaml
Copy application/nginx-with-request.yaml to clipboard
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  selector:
    matchLabels:
      app: nginx
  replicas: 2
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        resources:
          limits:
            memory: "128Mi"
            cpu: "500m"
        ports:
        - containerPort: 80
Create deployment by running following command:

kubectl apply -f https://k8s.io/examples/application/nginx-with-request.yaml
deployment.apps/nginx-deployment created
Check pod status by following command:

kubectl get pods
NAME                                READY   STATUS    RESTARTS   AGE
nginx-deployment-67d4bdd6f5-cx2nz   1/1     Running   0          13s
nginx-deployment-67d4bdd6f5-w6kd7   1/1     Running   0          13s
We can retrieve a lot more information about each of these pods using kubectl describe pod. For example:

kubectl describe pod nginx-deployment-67d4bdd6f5-w6kd7
Name:         nginx-deployment-67d4bdd6f5-w6kd7
Namespace:    default
Priority:     0
Node:         kube-worker-1/192.168.0.113
Start Time:   Thu, 17 Feb 2022 16:51:01 -0500
Labels:       app=nginx
              pod-template-hash=67d4bdd6f5
Annotations:  <none>
Status:       Running
IP:           10.88.0.3
IPs:
  IP:           10.88.0.3
  IP:           2001:db8::1
Controlled By:  ReplicaSet/nginx-deployment-67d4bdd6f5
Containers:
  nginx:
    Container ID:   containerd://5403af59a2b46ee5a23fb0ae4b1e077f7ca5c5fb7af16e1ab21c00e0e616462a
    Image:          nginx
    Image ID:       docker.io/library/nginx@sha256:2834dc507516af02784808c5f48b7cbe38b8ed5d0f4837f16e78d00deb7e7767
    Port:           80/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Thu, 17 Feb 2022 16:51:05 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     500m
      memory:  128Mi
    Requests:
      cpu:        500m
      memory:     128Mi
    Environment:  <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-bgsgp (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
Volumes:
  kube-api-access-bgsgp:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   Guaranteed
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  34s   default-scheduler  Successfully assigned default/nginx-deployment-67d4bdd6f5-w6kd7 to kube-worker-1
  Normal  Pulling    31s   kubelet            Pulling image "nginx"
  Normal  Pulled     30s   kubelet            Successfully pulled image "nginx" in 1.146417389s
  Normal  Created    30s   kubelet            Created container nginx
  Normal  Started    30s   kubelet            Started container nginx
Here you can see configuration information about the container(s) and Pod (labels, resource requirements, etc.), as well as status information about the container(s) and Pod (state, readiness, restart count, events, etc.).

The container state is one of Waiting, Running, or Terminated. Depending on the state, additional information will be provided - here you can see that for a container in Running state, the system tells you when the container started.

Ready tells you whether the container passed its last readiness probe. (In this case, the container does not have a readiness probe configured; the container is assumed to be ready if no readiness probe is configured.)

Restart Count tells you how many times the container has been restarted; this information can be useful for detecting crash loops in containers that are configured with a restart policy of Always.

Currently the only Condition associated with a Pod is the binary Ready condition, which indicates that the pod is able to service requests and should be added to the load balancing pools of all matching services.

Lastly, you see a log of recent events related to your Pod. "From" indicates the component that is logging the event. "Reason" and "Message" tell you what happened.

Example: debugging Pending Pods
A common scenario that you can detect using events is when you've created a Pod that won't fit on any node. For example, the Pod might request more resources than are free on any node, or it might specify a label selector that doesn't match any nodes. Let's say we created the previous Deployment with 5 replicas (instead of 2) and requesting 600 millicores instead of 500, on a four-node cluster where each (virtual) machine has 1 CPU. In that case one of the Pods will not be able to schedule. (Note that because of the cluster addon pods such as fluentd, skydns, etc., that run on each node, if we requested 1000 millicores then none of the Pods would be able to schedule.)

kubectl get pods
NAME                                READY     STATUS    RESTARTS   AGE
nginx-deployment-1006230814-6winp   1/1       Running   0          7m
nginx-deployment-1006230814-fmgu3   1/1       Running   0          7m
nginx-deployment-1370807587-6ekbw   1/1       Running   0          1m
nginx-deployment-1370807587-fg172   0/1       Pending   0          1m
nginx-deployment-1370807587-fz9sd   0/1       Pending   0          1m
To find out why the nginx-deployment-1370807587-fz9sd pod is not running, we can use kubectl describe pod on the pending Pod and look at its events:

kubectl describe pod nginx-deployment-1370807587-fz9sd
  Name:		nginx-deployment-1370807587-fz9sd
  Namespace:	default
  Node:		/
  Labels:		app=nginx,pod-template-hash=1370807587
  Status:		Pending
  IP:
  Controllers:	ReplicaSet/nginx-deployment-1370807587
  Containers:
    nginx:
      Image:	nginx
      Port:	80/TCP
      QoS Tier:
        memory:	Guaranteed
        cpu:	Guaranteed
      Limits:
        cpu:	1
        memory:	128Mi
      Requests:
        cpu:	1
        memory:	128Mi
      Environment Variables:
  Volumes:
    default-token-4bcbi:
      Type:	Secret (a volume populated by a Secret)
      SecretName:	default-token-4bcbi
  Events:
    FirstSeen	LastSeen	Count	From			        SubobjectPath	Type		Reason			    Message
    ---------	--------	-----	----			        -------------	--------	------			    -------
    1m		    48s		    7	    {default-scheduler }			        Warning		FailedScheduling	pod (nginx-deployment-1370807587-fz9sd) failed to fit in any node
  fit failure on node (kubernetes-node-6ta5): Node didn't have enough resource: CPU, requested: 1000, used: 1420, capacity: 2000
  fit failure on node (kubernetes-node-wul5): Node didn't have enough resource: CPU, requested: 1000, used: 1100, capacity: 2000
Here you can see the event generated by the scheduler saying that the Pod failed to schedule for reason FailedScheduling (and possibly others). The message tells us that there were not enough resources for the Pod on any of the nodes.

To correct this situation, you can use kubectl scale to update your Deployment to specify four or fewer replicas. (Or you could leave the one Pod pending, which is harmless.)

Events such as the ones you saw at the end of kubectl describe pod are persisted in etcd and provide high-level information on what is happening in the cluster. To list all events you can use

kubectl get events
but you have to remember that events are namespaced. This means that if you're interested in events for some namespaced object (e.g. what happened with Pods in namespace my-namespace) you need to explicitly provide a namespace to the command:

kubectl get events --namespace=my-namespace
To see events from all namespaces, you can use the --all-namespaces argument.

In addition to kubectl describe pod, another way to get extra information about a pod (beyond what is provided by kubectl get pod) is to pass the -o yaml output format flag to kubectl get pod. This will give you, in YAML format, even more information than kubectl describe pod - essentially all of the information the system has about the Pod. Here you will see things like annotations (which are key-value metadata without the label restrictions, that is used internally by Kubernetes system components), restart policy, ports, and volumes.

kubectl get pod nginx-deployment-1006230814-6winp -o yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: "2022-02-17T21:51:01Z"
  generateName: nginx-deployment-67d4bdd6f5-
  labels:
    app: nginx
    pod-template-hash: 67d4bdd6f5
  name: nginx-deployment-67d4bdd6f5-w6kd7
  namespace: default
  ownerReferences:
  - apiVersion: apps/v1
    blockOwnerDeletion: true
    controller: true
    kind: ReplicaSet
    name: nginx-deployment-67d4bdd6f5
    uid: 7d41dfd4-84c0-4be4-88ab-cedbe626ad82
  resourceVersion: "1364"
  uid: a6501da1-0447-4262-98eb-c03d4002222e
spec:
  containers:
  - image: nginx
    imagePullPolicy: Always
    name: nginx
    ports:
    - containerPort: 80
      protocol: TCP
    resources:
      limits:
        cpu: 500m
        memory: 128Mi
      requests:
        cpu: 500m
        memory: 128Mi
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: kube-api-access-bgsgp
      readOnly: true
  dnsPolicy: ClusterFirst
  enableServiceLinks: true
  nodeName: kube-worker-1
  preemptionPolicy: PreemptLowerPriority
  priority: 0
  restartPolicy: Always
  schedulerName: default-scheduler
  securityContext: {}
  serviceAccount: default
  serviceAccountName: default
  terminationGracePeriodSeconds: 30
  tolerations:
  - effect: NoExecute
    key: node.kubernetes.io/not-ready
    operator: Exists
    tolerationSeconds: 300
  - effect: NoExecute
    key: node.kubernetes.io/unreachable
    operator: Exists
    tolerationSeconds: 300
  volumes:
  - name: kube-api-access-bgsgp
    projected:
      defaultMode: 420
      sources:
      - serviceAccountToken:
          expirationSeconds: 3607
          path: token
      - configMap:
          items:
          - key: ca.crt
            path: ca.crt
          name: kube-root-ca.crt
      - downwardAPI:
          items:
          - fieldRef:
              apiVersion: v1
              fieldPath: metadata.namespace
            path: namespace
status:
  conditions:
  - lastProbeTime: null
    lastTransitionTime: "2022-02-17T21:51:01Z"
    status: "True"
    type: Initialized
  - lastProbeTime: null
    lastTransitionTime: "2022-02-17T21:51:06Z"
    status: "True"
    type: Ready
  - lastProbeTime: null
    lastTransitionTime: "2022-02-17T21:51:06Z"
    status: "True"
    type: ContainersReady
  - lastProbeTime: null
    lastTransitionTime: "2022-02-17T21:51:01Z"
    status: "True"
    type: PodScheduled
  containerStatuses:
  - containerID: containerd://5403af59a2b46ee5a23fb0ae4b1e077f7ca5c5fb7af16e1ab21c00e0e616462a
    image: docker.io/library/nginx:latest
    imageID: docker.io/library/nginx@sha256:2834dc507516af02784808c5f48b7cbe38b8ed5d0f4837f16e78d00deb7e7767
    lastState: {}
    name: nginx
    ready: true
    restartCount: 0
    started: true
    state:
      running:
        startedAt: "2022-02-17T21:51:05Z"
  hostIP: 192.168.0.113
  phase: Running
  podIP: 10.88.0.3
  podIPs:
  - ip: 10.88.0.3
  - ip: 2001:db8::1
  qosClass: Guaranteed
  startTime: "2022-02-17T21:51:01Z"
Examining pod logs
First, look at the logs of the affected container:

kubectl logs ${POD_NAME} -c ${CONTAINER_NAME}
If your container has previously crashed, you can access the previous container's crash log with:

kubectl logs ${POD_NAME} -c ${CONTAINER_NAME} --previous
Debugging with container exec
If the container image includes debugging utilities, as is the case with images built from Linux and Windows OS base images, you can run commands inside a specific container with kubectl exec:

kubectl exec ${POD_NAME} -c ${CONTAINER_NAME} -- ${CMD} ${ARG1} ${ARG2} ... ${ARGN}
Note:
-c ${CONTAINER_NAME} is optional. You can omit it for Pods that only contain a single container.
As an example, to look at the logs from a running Cassandra pod, you might run

kubectl exec cassandra -- cat /var/log/cassandra/system.log
You can run a shell that's connected to your terminal using the -i and -t arguments to kubectl exec, for example:

kubectl exec -it cassandra -- sh
For more details, see Get a Shell to a Running Container.

Debugging with an ephemeral debug container
FEATURE STATE: Kubernetes v1.25 [stable]
Ephemeral containers are useful for interactive troubleshooting when kubectl exec is insufficient because a container has crashed or a container image doesn't include debugging utilities, such as with distroless images.

Example debugging using ephemeral containers
You can use the kubectl debug command to add ephemeral containers to a running Pod. First, create a pod for the example:

kubectl run ephemeral-demo --image=registry.k8s.io/pause:3.1 --restart=Never
The examples in this section use the pause container image because it does not contain debugging utilities, but this method works with all container images.

If you attempt to use kubectl exec to create a shell you will see an error because there is no shell in this container image.

kubectl exec -it ephemeral-demo -- sh
OCI runtime exec failed: exec failed: container_linux.go:346: starting container process caused "exec: \"sh\": executable file not found in $PATH": unknown
You can instead add a debugging container using kubectl debug. If you specify the -i/--interactive argument, kubectl will automatically attach to the console of the Ephemeral Container.

kubectl debug -it ephemeral-demo --image=busybox:1.28 --target=ephemeral-demo
Defaulting debug container name to debugger-8xzrl.
If you don't see a command prompt, try pressing enter.
/ #
This command adds a new busybox container and attaches to it. The --target parameter targets the process namespace of another container. It's necessary here because kubectl run does not enable process namespace sharing in the pod it creates.

Note:
The --target parameter must be supported by the Container Runtime. When not supported, the Ephemeral Container may not be started, or it may be started with an isolated process namespace so that ps does not reveal processes in other containers.
You can view the state of the newly created ephemeral container using kubectl describe:

kubectl describe pod ephemeral-demo
...
Ephemeral Containers:
  debugger-8xzrl:
    Container ID:   docker://b888f9adfd15bd5739fefaa39e1df4dd3c617b9902082b1cfdc29c4028ffb2eb
    Image:          busybox
    Image ID:       docker-pullable://busybox@sha256:1828edd60c5efd34b2bf5dd3282ec0cc04d47b2ff9caa0b6d4f07a21d1c08084
    Port:           <none>
    Host Port:      <none>
    State:          Running
      Started:      Wed, 12 Feb 2020 14:25:42 +0100
    Ready:          False
    Restart Count:  0
    Environment:    <none>
    Mounts:         <none>
...
Use kubectl delete to remove the Pod when you're finished:

kubectl delete pod ephemeral-demo
Debugging using a copy of the Pod
Sometimes Pod configuration options make it difficult to troubleshoot in certain situations. For example, you can't run kubectl exec to troubleshoot your container if your container image does not include a shell or if your application crashes on startup. In these situations you can use kubectl debug to create a copy of the Pod with configuration values changed to aid debugging.

Copying a Pod while adding a new container
Adding a new container can be useful when your application is running but not behaving as you expect and you'd like to add additional troubleshooting utilities to the Pod.

For example, maybe your application's container images are built on busybox but you need debugging utilities not included in busybox. You can simulate this scenario using kubectl run:

kubectl run myapp --image=busybox:1.28 --restart=Never -- sleep 1d
Run this command to create a copy of myapp named myapp-debug that adds a new Ubuntu container for debugging:

kubectl debug myapp -it --image=ubuntu --share-processes --copy-to=myapp-debug
Defaulting debug container name to debugger-w7xmf.
If you don't see a command prompt, try pressing enter.
root@myapp-debug:/#
Note:
kubectl debug automatically generates a container name if you don't choose one using the --container flag.
The -i flag causes kubectl debug to attach to the new container by default. You can prevent this by specifying --attach=false. If your session becomes disconnected you can reattach using kubectl attach.
The --share-processes allows the containers in this Pod to see processes from the other containers in the Pod. For more information about how this works, see Share Process Namespace between Containers in a Pod.
Don't forget to clean up the debugging Pod when you're finished with it:

kubectl delete pod myapp myapp-debug
Copying a Pod while changing its command
Sometimes it's useful to change the command for a container, for example to add a debugging flag or because the application is crashing.

To simulate a crashing application, use kubectl run to create a container that immediately exits:

kubectl run --image=busybox:1.28 myapp -- false
You can see using kubectl describe pod myapp that this container is crashing:

Containers:
  myapp:
    Image:         busybox
    ...
    Args:
      false
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
You can use kubectl debug to create a copy of this Pod with the command changed to an interactive shell:

kubectl debug myapp -it --copy-to=myapp-debug --container=myapp -- sh
If you don't see a command prompt, try pressing enter.
/ #
Now you have an interactive shell that you can use to perform tasks like checking filesystem paths or running the container command manually.

Note:
To change the command of a specific container you must specify its name using --container or kubectl debug will instead create a new container to run the command you specified.
The -i flag causes kubectl debug to attach to the container by default. You can prevent this by specifying --attach=false. If your session becomes disconnected you can reattach using kubectl attach.
Don't forget to clean up the debugging Pod when you're finished with it:

kubectl delete pod myapp myapp-debug
Copying a Pod while changing container images
In some situations you may want to change a misbehaving Pod from its normal production container images to an image containing a debugging build or additional utilities.

As an example, create a Pod using kubectl run:

kubectl run myapp --image=busybox:1.28 --restart=Never -- sleep 1d
Now use kubectl debug to make a copy and change its container image to ubuntu:

kubectl debug myapp --copy-to=myapp-debug --set-image=*=ubuntu
The syntax of --set-image uses the same container_name=image syntax as kubectl set image. *=ubuntu means change the image of all containers to ubuntu.

Don't forget to clean up the debugging Pod when you're finished with it:

kubectl delete pod myapp myapp-debug
Debugging via a shell on the node
If none of these approaches work, you can find the Node on which the Pod is running and create a Pod running on the Node. To create an interactive shell on a Node using kubectl debug, run:

kubectl debug node/mynode -it --image=ubuntu
Creating debugging pod node-debugger-mynode-pdx84 with container debugger on node mynode.
If you don't see a command prompt, try pressing enter.
root@ek8s:/#
When creating a debugging session on a node, keep in mind that:

kubectl debug automatically generates the name of the new Pod based on the name of the Node.
The root filesystem of the Node will be mounted at /host.
The container runs in the host IPC, Network, and PID namespaces, although the pod isn't privileged, so reading some process information may fail, and chroot /host may fail.
If you need a privileged pod, create it manually or use the --profile=sysadmin flag.
Don't forget to clean up the debugging Pod when you're finished with it:

kubectl delete pod node-debugger-mynode-pdx84
Capturing and analyzing Node/Pod traffic
When debugging networking issues, capturing and analyzing network traffic from Nodes/Pods can provide valuable insights into connectivity problems, DNS resolution failures, or unexpected network behavior.

You can use kubectl debug with the --profile=sysadmin flag to run network capture tools on a node. First, create a debugging session on the node where your Pod is running:

kubectl debug --profile=sysadmin node/${NODE_NAME} -it --image=ubuntu:latest
Once inside the debug container, install tcpdump and capture traffic on the node's network interfaces:

apt-get update && apt-get install -y tcpdump
tcpdump -i any -n
Note:
Don't forget to clean up the debugging Pod when you're finished with it:

kubectl delete pod node-debugger-mynode-pdx84
You can also capture traffic from a specific Pod:

kubectl debug --profile=sysadmin pod/${POD_NAME} -n ${NAMESPACE} -it --image=ubuntu:latest
And then perform the same tcpdump command inside the debug container to capture traffic from the Pod's network namespace.

Debugging a Pod or Node while applying a profile
When using kubectl debug to debug a node via a debugging Pod, a Pod via an ephemeral container, or a copied Pod, you can apply a profile to them. By applying a profile, specific properties such as securityContext are set, allowing for adaptation to various scenarios. There are two types of profiles, static profile and custom profile.

Applying a Static Profile
A static profile is a set of predefined properties, and you can apply them using the --profile flag. The available profiles are as follows:

Profile	Description
legacy	A set of properties backwards compatibility with 1.22 behavior
general	A reasonable set of generic properties for each debugging journey
baseline	A set of properties compatible with PodSecurityStandard baseline policy
restricted	A set of properties compatible with PodSecurityStandard restricted policy
netadmin	A set of properties including Network Administrator privileges
sysadmin	A set of properties including System Administrator (root) privileges
Note:
If you don't specify --profile, the legacy profile is used by default, but it is planned to be deprecated in the near future. So it is recommended to use other profiles such as general.
Assume that you create a Pod and debug it. First, create a Pod named myapp as an example:

kubectl run myapp --image=busybox:1.28 --restart=Never -- sleep 1d
Then, debug the Pod using an ephemeral container. If the ephemeral container needs to have privilege, you can use the sysadmin profile:

kubectl debug -it myapp --image=busybox:1.28 --target=myapp --profile=sysadmin
Targeting container "myapp". If you don't see processes from this container it may be because the container runtime doesn't support this feature.
Defaulting debug container name to debugger-6kg4x.
If you don't see a command prompt, try pressing enter.
/ #
Check the capabilities of the ephemeral container process by running the following command inside the container:

/ # grep Cap /proc/$$/status
...
CapPrm:	000001ffffffffff
CapEff:	000001ffffffffff
...
This means the container process is granted full capabilities as a privileged container by applying sysadmin profile. See more details about capabilities.

You can also check that the ephemeral container was created as a privileged container:

kubectl get pod myapp -o jsonpath='{.spec.ephemeralContainers[0].securityContext}'
{"privileged":true}
Clean up the Pod when you're finished with it:

kubectl delete pod myapp
Applying Custom Profile
FEATURE STATE: Kubernetes v1.32 [stable]
You can define a partial container spec for debugging as a custom profile in either YAML or JSON format, and apply it using the --custom flag.

Note:
Custom profile only supports the modification of the container spec, but modifications to name, image, command, lifecycle and volumeDevices fields of the container spec are not allowed. It does not support the modification of the Pod spec.
Create a Pod named myapp as an example:

kubectl run myapp --image=busybox:1.28 --restart=Never -- sleep 1d
Create a custom profile in YAML or JSON format. Here, create a YAML format file named custom-profile.yaml:

env:
- name: ENV_VAR_1
  value: value_1
- name: ENV_VAR_2
  value: value_2
securityContext:
  capabilities:
    add:
    - NET_ADMIN
    - SYS_TIME
Run this command to debug the Pod using an ephemeral container with the custom profile:

kubectl debug -it myapp --image=busybox:1.28 --target=myapp --profile=general --custom=custom-profile.yaml
You can check that the ephemeral container has been added to the target Pod with the custom profile applied:

kubectl get pod myapp -o jsonpath='{.spec.ephemeralContainers[0].env}'
[{"name":"ENV_VAR_1","value":"value_1"},{"name":"ENV_VAR_2","value":"value_2"}]
kubectl get pod myapp -o jsonpath='{.spec.ephemeralContainers[0].securityContext}'
{"capabilities":{"add":["NET_ADMIN","SYS_TIME"]}}
Clean up the Pod when you're finished with it:

kubectl delete pod myapp

Get a Shell to a Running Container
This page shows how to use kubectl exec to get a shell to a running container.

Before you begin
You need to have a Kubernetes cluster, and the kubectl command-line tool must be configured to communicate with your cluster. It is recommended to run this tutorial on a cluster with at least two nodes that are not acting as control plane hosts. If you do not already have a cluster, you can create one by using minikube or you can use one of these Kubernetes playgrounds:

iximiuz Labs
Killercoda
KodeKloud
Getting a shell to a container
In this exercise, you create a Pod that has one container. The container runs the nginx image. Here is the configuration file for the Pod:

application/shell-demo.yaml
Copy application/shell-demo.yaml to clipboard
apiVersion: v1
kind: Pod
metadata:
  name: shell-demo
spec:
  volumes:
  - name: shared-data
    emptyDir: {}
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
  hostNetwork: true
  dnsPolicy: Default
Create the Pod:

kubectl apply -f https://k8s.io/examples/application/shell-demo.yaml
Verify that the container is running:

kubectl get pod shell-demo
Get a shell to the running container:

kubectl exec --stdin --tty shell-demo -- /bin/bash
Note:
The double dash (--) separates the arguments you want to pass to the command from the kubectl arguments.
In your shell, list the root directory:

# Run this inside the container
ls /
In your shell, experiment with other commands. Here are some examples:

# You can run these example commands inside the container
ls /
cat /proc/mounts
cat /proc/1/maps
apt-get update
apt-get install -y tcpdump
tcpdump
apt-get install -y lsof
lsof
apt-get install -y procps
ps aux
ps aux | grep nginx
Writing the root page for nginx
Look again at the configuration file for your Pod. The Pod has an emptyDir volume, and the container mounts the volume at /usr/share/nginx/html.

In your shell, create an index.html file in the /usr/share/nginx/html directory:

# Run this inside the container
echo 'Hello shell demo' > /usr/share/nginx/html/index.html
In your shell, send a GET request to the nginx server:

# Run this in the shell inside your container
apt-get update
apt-get install curl
curl http://localhost/
The output shows the text that you wrote to the index.html file:

Hello shell demo
When you are finished with your shell, enter exit.

exit # To quit the shell in the container
Running individual commands in a container
In an ordinary command window, not your shell, list the environment variables in the running container:

kubectl exec shell-demo -- env
Experiment with running other commands. Here are some examples:

kubectl exec shell-demo -- ps aux
kubectl exec shell-demo -- ls /
kubectl exec shell-demo -- cat /proc/1/mounts
Opening a shell when a Pod has more than one container
If a Pod has more than one container, use --container or -c to specify a container in the kubectl exec command. For example, suppose you have a Pod named my-pod, and the Pod has two containers named main-app and helper-app. The following command would open a shell to the main-app container.

kubectl exec -i -t my-pod --container main-app -- /bin/bash
Note:
The short options -i and -t are the same as the long options --stdin and --tty

Troubleshooting Clusters
Debugging common cluster issues.
This doc is about cluster troubleshooting; we assume you have already ruled out your application as the root cause of the problem you are experiencing. See the application troubleshooting guide for tips on application debugging. You may also visit the troubleshooting overview document for more information.

For troubleshooting kubectl, refer to Troubleshooting kubectl.

Listing your cluster
The first thing to debug in your cluster is if your nodes are all registered correctly.

Run the following command:

kubectl get nodes
And verify that all of the nodes you expect to see are present and that they are all in the Ready state.

To get detailed information about the overall health of your cluster, you can run:

kubectl cluster-info dump
Example: debugging a down/unreachable node
Sometimes when debugging it can be useful to look at the status of a node -- for example, because you've noticed strange behavior of a Pod that's running on the node, or to find out why a Pod won't schedule onto the node. As with Pods, you can use kubectl describe node and kubectl get node -o yaml to retrieve detailed information about nodes. For example, here's what you'll see if a node is down (disconnected from the network, or kubelet dies and won't restart, etc.). Notice the events that show the node is NotReady, and also notice that the pods are no longer running (they are evicted after five minutes of NotReady status).

kubectl get nodes
NAME                     STATUS       ROLES     AGE     VERSION
kube-worker-1            NotReady     <none>    1h      v1.23.3
kubernetes-node-bols     Ready        <none>    1h      v1.23.3
kubernetes-node-st6x     Ready        <none>    1h      v1.23.3
kubernetes-node-unaj     Ready        <none>    1h      v1.23.3
kubectl describe node kube-worker-1
Name:               kube-worker-1
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
                    kubernetes.io/hostname=kube-worker-1
                    kubernetes.io/os=linux
                    node.alpha.kubernetes.io/ttl: 0
                    volumes.kubernetes.io/controller-managed-attach-detach: true
CreationTimestamp:  Thu, 17 Feb 2022 16:46:30 -0500
Taints:             node.kubernetes.io/unreachable:NoExecute
                    node.kubernetes.io/unreachable:NoSchedule
Unschedulable:      false
Lease:
  HolderIdentity:  kube-worker-1
  AcquireTime:     <unset>
  RenewTime:       Thu, 17 Feb 2022 17:13:09 -0500
Conditions:
  Type                 Status    LastHeartbeatTime                 LastTransitionTime                Reason              Message
  ----                 ------    -----------------                 ------------------                ------              -------
  NetworkUnavailable   False     Thu, 17 Feb 2022 17:09:13 -0500   Thu, 17 Feb 2022 17:09:13 -0500   WeaveIsUp           Weave pod has set this
  MemoryPressure       Unknown   Thu, 17 Feb 2022 17:12:40 -0500   Thu, 17 Feb 2022 17:13:52 -0500   NodeStatusUnknown   Kubelet stopped posting node status.
  DiskPressure         Unknown   Thu, 17 Feb 2022 17:12:40 -0500   Thu, 17 Feb 2022 17:13:52 -0500   NodeStatusUnknown   Kubelet stopped posting node status.
  PIDPressure          Unknown   Thu, 17 Feb 2022 17:12:40 -0500   Thu, 17 Feb 2022 17:13:52 -0500   NodeStatusUnknown   Kubelet stopped posting node status.
  Ready                Unknown   Thu, 17 Feb 2022 17:12:40 -0500   Thu, 17 Feb 2022 17:13:52 -0500   NodeStatusUnknown   Kubelet stopped posting node status.
Addresses:
  InternalIP:  192.168.0.113
  Hostname:    kube-worker-1
Capacity:
  cpu:                2
  ephemeral-storage:  15372232Ki
  hugepages-2Mi:      0
  memory:             2025188Ki
  pods:               110
Allocatable:
  cpu:                2
  ephemeral-storage:  14167048988
  hugepages-2Mi:      0
  memory:             1922788Ki
  pods:               110
System Info:
  Machine ID:                 9384e2927f544209b5d7b67474bbf92b
  System UUID:                aa829ca9-73d7-064d-9019-df07404ad448
  Boot ID:                    5a295a03-aaca-4340-af20-1327fa5dab5c
  Kernel Version:             5.13.0-28-generic
  OS Image:                   Ubuntu 21.10
  Operating System:           linux
  Architecture:               amd64
  Container Runtime Version:  containerd://1.5.9
  Kubelet Version:            v1.23.3
  Kube-Proxy Version:         v1.23.3
Non-terminated Pods:          (4 in total)
  Namespace                   Name                                 CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age
  ---------                   ----                                 ------------  ----------  ---------------  -------------  ---
  default                     nginx-deployment-67d4bdd6f5-cx2nz    500m (25%)    500m (25%)  128Mi (6%)       128Mi (6%)     23m
  default                     nginx-deployment-67d4bdd6f5-w6kd7    500m (25%)    500m (25%)  128Mi (6%)       128Mi (6%)     23m
  kube-system                 kube-proxy-dnxbz                     0 (0%)        0 (0%)      0 (0%)           0 (0%)         28m
  kube-system                 weave-net-gjxxp                      100m (5%)     0 (0%)      200Mi (10%)      0 (0%)         28m
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests     Limits
  --------           --------     ------
  cpu                1100m (55%)  1 (50%)
  memory             456Mi (24%)  256Mi (13%)
  ephemeral-storage  0 (0%)       0 (0%)
  hugepages-2Mi      0 (0%)       0 (0%)
Events:
...
kubectl get node kube-worker-1 -o yaml
apiVersion: v1
kind: Node
metadata:
  annotations:
    node.alpha.kubernetes.io/ttl: "0"
    volumes.kubernetes.io/controller-managed-attach-detach: "true"
  creationTimestamp: "2022-02-17T21:46:30Z"
  labels:
    beta.kubernetes.io/arch: amd64
    beta.kubernetes.io/os: linux
    kubernetes.io/arch: amd64
    kubernetes.io/hostname: kube-worker-1
    kubernetes.io/os: linux
  name: kube-worker-1
  resourceVersion: "4026"
  uid: 98efe7cb-2978-4a0b-842a-1a7bf12c05f8
spec: {}
status:
  addresses:
  - address: 192.168.0.113
    type: InternalIP
  - address: kube-worker-1
    type: Hostname
  allocatable:
    cpu: "2"
    ephemeral-storage: "14167048988"
    hugepages-2Mi: "0"
    memory: 1922788Ki
    pods: "110"
  capacity:
    cpu: "2"
    ephemeral-storage: 15372232Ki
    hugepages-2Mi: "0"
    memory: 2025188Ki
    pods: "110"
  conditions:
  - lastHeartbeatTime: "2022-02-17T22:20:32Z"
    lastTransitionTime: "2022-02-17T22:20:32Z"
    message: Weave pod has set this
    reason: WeaveIsUp
    status: "False"
    type: NetworkUnavailable
  - lastHeartbeatTime: "2022-02-17T22:20:15Z"
    lastTransitionTime: "2022-02-17T22:13:25Z"
    message: kubelet has sufficient memory available
    reason: KubeletHasSufficientMemory
    status: "False"
    type: MemoryPressure
  - lastHeartbeatTime: "2022-02-17T22:20:15Z"
    lastTransitionTime: "2022-02-17T22:13:25Z"
    message: kubelet has no disk pressure
    reason: KubeletHasNoDiskPressure
    status: "False"
    type: DiskPressure
  - lastHeartbeatTime: "2022-02-17T22:20:15Z"
    lastTransitionTime: "2022-02-17T22:13:25Z"
    message: kubelet has sufficient PID available
    reason: KubeletHasSufficientPID
    status: "False"
    type: PIDPressure
  - lastHeartbeatTime: "2022-02-17T22:20:15Z"
    lastTransitionTime: "2022-02-17T22:15:15Z"
    message: kubelet is posting ready status
    reason: KubeletReady
    status: "True"
    type: Ready
  daemonEndpoints:
    kubeletEndpoint:
      Port: 10250
  nodeInfo:
    architecture: amd64
    bootID: 22333234-7a6b-44d4-9ce1-67e31dc7e369
    containerRuntimeVersion: containerd://1.5.9
    kernelVersion: 5.13.0-28-generic
    kubeProxyVersion: v1.23.3
    kubeletVersion: v1.23.3
    machineID: 9384e2927f544209b5d7b67474bbf92b
    operatingSystem: linux
    osImage: Ubuntu 21.10
    systemUUID: aa829ca9-73d7-064d-9019-df07404ad448
Looking at logs
For now, digging deeper into the cluster requires logging into the relevant machines. Here are the locations of the relevant log files. On systemd-based systems, you may need to use journalctl instead of examining log files.

Control Plane nodes
/var/log/kube-apiserver.log - API Server, responsible for serving the API
/var/log/kube-scheduler.log - Scheduler, responsible for making scheduling decisions
/var/log/kube-controller-manager.log - a component that runs most Kubernetes built-in controllers, with the notable exception of scheduling (the kube-scheduler handles scheduling).
Worker Nodes
/var/log/kubelet.log - logs from the kubelet, responsible for running containers on the node
/var/log/kube-proxy.log - logs from kube-proxy, which is responsible for directing traffic to Service endpoints
Cluster failure modes
This is an incomplete list of things that could go wrong, and how to adjust your cluster setup to mitigate the problems.

Contributing causes
VM(s) shutdown
Network partition within cluster, or between cluster and users
Crashes in Kubernetes software
Data loss or unavailability of persistent storage (e.g. GCE PD or AWS EBS volume)
Operator error, for example, misconfigured Kubernetes software or application software
Specific scenarios
API server VM shutdown or apiserver crashing
Results
unable to stop, update, or start new pods, services, replication controller
existing pods and services should continue to work normally unless they depend on the Kubernetes API
API server backing storage lost
Results
the kube-apiserver component fails to start successfully and become healthy
kubelets will not be able to reach it but will continue to run the same pods and provide the same service proxying
manual recovery or recreation of apiserver state necessary before apiserver is restarted
Supporting services (node controller, replication controller manager, scheduler, etc) VM shutdown or crashes
currently those are colocated with the apiserver, and their unavailability has similar consequences as apiserver
in future, these will be replicated as well and may not be co-located
they do not have their own persistent state
Individual node (VM or physical machine) shuts down
Results
pods on that Node stop running
Network partition
Results
partition A thinks the nodes in partition B are down; partition B thinks the apiserver is down. (Assuming the master VM ends up in partition A.)
Kubelet software fault
Results
crashing kubelet cannot start new pods on the node
kubelet might delete the pods or not
node marked unhealthy
replication controllers start new pods elsewhere
Cluster operator error
Results
loss of pods, services, etc
lost of apiserver backing store
users unable to read API
etc.
Mitigations
Action: Use the IaaS provider's automatic VM restarting feature for IaaS VMs

Mitigates: Apiserver VM shutdown or apiserver crashing
Mitigates: Supporting services VM shutdown or crashes
Action: Use IaaS providers reliable storage (e.g. GCE PD or AWS EBS volume) for VMs with apiserver+etcd

Mitigates: Apiserver backing storage lost
Action: Use high-availability configuration

Mitigates: Control plane node shutdown or control plane components (scheduler, API server, controller-manager) crashing
Will tolerate one or more simultaneous node or component failures
Mitigates: API server backing storage (i.e., etcd's data directory) lost
Assumes HA (highly-available) etcd configuration
Action: Snapshot apiserver PDs/EBS-volumes periodically

Mitigates: Apiserver backing storage lost
Mitigates: Some cases of operator error
Mitigates: Some cases of Kubernetes software fault
Action: use replication controller and services in front of pods

Mitigates: Node shutdown
Mitigates: Kubelet software fault
Action: applications (containers) designed to tolerate unexpected restarts

Mitigates: Node shutdown
Mitigates: Kubelet software fault
What's next
Learn about the metrics available in the Resource Metrics Pipeline
Discover additional tools for monitoring resource usage
Use Node Problem Detector to monitor node health
Use kubectl debug node to debug Kubernetes nodes
Use crictl to debug Kubernetes nodes
Get more information about Kubernetes auditing
Use telepresence to develop and debug services locally

Metrics For Kubernetes System Components
System component metrics can give a better look into what is happening inside them. Metrics are particularly useful for building dashboards and alerts.

Kubernetes components emit metrics in Prometheus format. This format is structured plain text, designed so that people and machines can both read it.

Metrics in Kubernetes
In most cases metrics are available on /metrics endpoint of the HTTP server. For components that don't expose endpoint by default, it can be enabled using --bind-address flag.

Examples of those components:

kube-controller-manager
kube-proxy
kube-apiserver
kube-scheduler
kubelet
In a production environment you may want to configure Prometheus Server or some other metrics scraper to periodically gather these metrics and make them available in some kind of time series database.

Note that kubelet also exposes metrics in /metrics/cadvisor, /metrics/resource and /metrics/probes endpoints. Those metrics do not have the same lifecycle.

If your cluster uses RBAC, reading metrics requires authorization via a user, group or ServiceAccount with a ClusterRole that allows accessing /metrics. For example:

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - nonResourceURLs:
      - "/metrics"
    verbs:
      - get
Metric lifecycle
Alpha metric → Beta metric → Stable metric → Deprecated metric → Hidden metric → Deleted metric

Alpha metrics have no stability guarantees. These metrics can be modified or deleted at any time.

Beta metrics observe a looser API contract than its stable counterparts. No labels can be removed from beta metrics during their lifetime, however, labels can be added while the metric is in the beta stage.

Stable metrics are guaranteed to not change. This means:

A stable metric without a deprecated signature will not be deleted or renamed
A stable metric's type will not be modified
Deprecated metrics are slated for deletion, but are still available for use. These metrics include an annotation about the version in which they became deprecated.

For example:

Before deprecation

# HELP some_counter this counts things
# TYPE some_counter counter
some_counter 0
After deprecation

# HELP some_counter (Deprecated since 1.15.0) this counts things
# TYPE some_counter counter
some_counter 0
Hidden metrics are no longer published for scraping, but are still available for use. A deprecated metric becomes a hidden metric after a period of time, based on its stability level:

STABLE metrics become hidden after a minimum of 3 releases or 9 months, whichever is longer.
BETA metrics become hidden after a minimum of 1 release or 4 months, whichever is longer.
ALPHA metrics can be hidden or removed in the same release in which they are deprecated.
To use a hidden metric, you must enable it. For more details, refer to the Show hidden metrics section.

Deleted metrics are no longer published and cannot be used.

Show hidden metrics
As described above, admins can enable hidden metrics through a command-line flag on a specific binary. This intends to be used as an escape hatch for admins if they missed the migration of the metrics deprecated in the last release.

The flag show-hidden-metrics-for-version takes a version for which you want to show metrics deprecated in that release. The version is expressed as x.y, where x is the major version, y is the minor version. The patch version is not needed even though a metrics can be deprecated in a patch release, the reason for that is the metrics deprecation policy runs against the minor release.

The flag can only take the previous minor version as its value. If you want to show all metrics hidden in the previous release, you can set the show-hidden-metrics-for-version flag to the previous version. Using a version that is too old is not allowed because it violates the metrics deprecation policy.

For example, let's assume metric A is deprecated in 1.29. The version in which metric A becomes hidden depends on its stability level:

If metric A is ALPHA, it could be hidden in 1.29.
If metric A is BETA, it will be hidden in 1.30 at the earliest. If you are upgrading to 1.30 and still need A, you must use the command-line flag --show-hidden-metrics-for-version=1.29.
If metric A is STABLE, it will be hidden in 1.32 at the earliest. If you are upgrading to 1.32 and still need A, you must use the command-line flag --show-hidden-metrics-for-version=1.31.
Component metrics
kube-controller-manager metrics
Controller manager metrics provide important insight into the performance and health of the controller manager. These metrics include common Go language runtime metrics such as go_routine count and controller specific metrics such as etcd request latencies or Cloudprovider (AWS, GCE, OpenStack) API latencies that can be used to gauge the health of a cluster.

Starting from Kubernetes 1.7, detailed Cloudprovider metrics are available for storage operations for GCE, AWS, Vsphere and OpenStack. These metrics can be used to monitor health of persistent volume operations.

For example, for GCE these metrics are called:

cloudprovider_gce_api_request_duration_seconds { request = "instance_list"}
cloudprovider_gce_api_request_duration_seconds { request = "disk_insert"}
cloudprovider_gce_api_request_duration_seconds { request = "disk_delete"}
cloudprovider_gce_api_request_duration_seconds { request = "attach_disk"}
cloudprovider_gce_api_request_duration_seconds { request = "detach_disk"}
cloudprovider_gce_api_request_duration_seconds { request = "list_disk"}
kube-scheduler metrics
FEATURE STATE: Kubernetes v1.21 [beta]
The scheduler exposes optional metrics that reports the requested resources and the desired limits of all running pods. These metrics can be used to build capacity planning dashboards, assess current or historical scheduling limits, quickly identify workloads that cannot schedule due to lack of resources, and compare actual usage to the pod's request.

The kube-scheduler identifies the resource requests and limits configured for each Pod; when either a request or limit is non-zero, the kube-scheduler reports a metrics timeseries. The time series is labelled by:

namespace
pod name
the node where the pod is scheduled or an empty string if not yet scheduled
priority
the assigned scheduler for that pod
the name of the resource (for example, cpu)
the unit of the resource if known (for example, cores)
Once a pod reaches completion (has a restartPolicy of Never or OnFailure and is in the Succeeded or Failed pod phase, or has been deleted and all containers have a terminated state) the series is no longer reported since the scheduler is now free to schedule other pods to run. The two metrics are called kube_pod_resource_request and kube_pod_resource_limit.

The metrics are exposed at the HTTP endpoint /metrics/resources. They require authorization for the /metrics/resources endpoint, usually granted by a ClusterRole with the get verb for the /metrics/resources non-resource URL.

On Kubernetes 1.21 you must use the --show-hidden-metrics-for-version=1.20 flag to expose these alpha stability metrics.

kubelet Pressure Stall Information (PSI) metrics
FEATURE STATE: Kubernetes v1.36 [stable](enabled by default)
When the kernel has PSI enabled (version 4.20 or later), the kubelet collects Pressure Stall Information (PSI) for CPU, memory and I/O usage. The information is collected at node, pod and container level.

Prometheus Metrics: Exposed at the /metrics/cadvisor endpoint as cumulative counters (totals) representing the total stall time in seconds. The metrics are exposed at this endpoint with the following names:

container_pressure_cpu_stalled_seconds_total
container_pressure_cpu_waiting_seconds_total
container_pressure_memory_stalled_seconds_total
container_pressure_memory_waiting_seconds_total
container_pressure_io_stalled_seconds_total
container_pressure_io_waiting_seconds_total
Summary API: Exposed at the /stats/summary endpoint, providing both the cumulative totals and the moving averages (avg10, avg60, avg300) in a JSON format. These averages represent the percentage of time that tasks were stalled on a resource over the respective 10-second, 60-second, and 5-minute intervals.

These metrics are also natively exported through the node's respective file in /proc/pressure/ -- cpu, memory, and io in the following format:

some avg10=0.00 avg60=0.00 avg300=0.00 total=0
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
How can these metrics be interpreted together? Take for example the following query from the Summary API:
kubectl get --raw "/api/v1/nodes/$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')/proxy/stats/summary" | jq '.pods[].containers[] | select(.name=="<CONTAINER_NAME>") | {name, cpu: .cpu.psi, memory: .memory.psi, io: .io.psi}'. This returns the information in a json format as such.

{
  "name": "<CONTAINER_NAME>",
  "cpu": {
    "full": {
      "total": 0,
      "avg10": 0,
      "avg60": 0,
      "avg300": 0
    },
    "some": {
      "total": 35232438,
      "avg10": 0.74,
      "avg60": 0.52,
      "avg300": 0.21,
    },  
  },
  "memory": {
    "full": {
      "total": 539105,
      "avg10": 0,
      "avg60": 0,
      "avg300": 0
    },
    "some": {
      "total": 658164,
      "avg10": 0.01,
      "avg60": 0.01,
      "avg300": 0.00,
    },
    }
  },
  "io": {
    "full": {
      "total": 33190987,
      "avg10": 0.31,
      "avg60": 0.22,
      "avg300": 0.05,
    },
    "some": {
      "total": 40809937,
      "avg10": 0.52,
      "avg60": 0.45,
      "avg300": 0.12,
    }
  }
}
Here is a simple spike scenario. The cpu.some avg10 value of 0.74 indicates that in the last 10 seconds, at least one task in this container was stalled on the CPU for 0.74% of the time (0.0074 seconds or 74 milliseconds). Because avg10 (0.74) is significantly higher than avg300 (0.21) on the same resource, this suggests a recent surge in resource contention rather than a sustained long-term bottleneck. If monitored continuously and the avg300 metrics increase as well, we can diagnose a more serious, lasting issue!

Additionally, notice how in this example cpu.some shows pressure, while cpu.full remains at 0.00. This tells us that while some processes were delayed waiting for CPU time, the container as a whole was still making progress. A non-zero full value would indicate that all non-idle tasks were stalled simultaneously, a much bigger problem. Although not as human-readable, the total value of 35232438 represents the cumulative stall time in microseconds, that allow latency spike detection that otherwise may not show in the averages. They are also useful for monitoring systems, like Prometheus, to calculate precise rates of increase over specific time windows. As a final note, when observing high I/O Pressure alongside low Memory Pressure, it can indicate that the application is waiting on disk throughput rather than failing due to a lack of available RAM. The node is not over-committed on memory, and a different diagnosis for disk consumption can be investigated.

PSI metrics unlock a more robust way to monitor realitime resource contention at all levels for every cgroup, opening up the opportunity to dynamically handle workloads across the system. You can read more about the PSI metrics in Understand PSI Metrics.

Requirements
Pressure Stall Information requires:

Linux kernel versions 4.20 or later.
cgroup v2
Disabling metrics
You can explicitly turn off metrics via command line flag --disabled-metrics. This may be desired if, for example, a metric is causing a performance problem. The input is a list of disabled metrics (i.e. --disabled-metrics=metric1,metric2).

Metric cardinality enforcement
Metrics with unbounded dimensions could cause memory issues in the components they instrument. To limit resource use, you can use the --allow-metric-labels command line option to dynamically configure an allow-list of label values for a metric.

In alpha stage, the flag can only take in a series of mappings as metric label allow-list. Each mapping is of the format <metric_name>,<label_name>=<allowed_labels> where <allowed_labels> is a comma-separated list of acceptable label names.

The overall format looks like:

--allow-metric-labels <metric_name>,<label_name>='<allow_value1>, <allow_value2>...', <metric_name2>,<label_name>='<allow_value1>, <allow_value2>...', ...
Here is an example:

--allow-metric-labels number_count_metric,odd_number='1,3,5', number_count_metric,even_number='2,4,6', date_gauge_metric,weekend='Saturday,Sunday'
In addition to specifying this from the CLI, this can also be done within a configuration file. You can specify the path to that configuration file using the --allow-metric-labels-manifest command line argument to a component. Here's an example of the contents of that configuration file:

"metric1,label2": "v1,v2,v3"
"metric2,label1": "v1,v2,v3"
Additionally, the cardinality_enforcement_unexpected_categorizations_total meta-metric records the count of unexpected categorizations during cardinality enforcement, that is, whenever a label value is encountered that is not allowed with respect to the allow-list constraints

Traces For Kubernetes System Components
FEATURE STATE: Kubernetes v1.27 [beta]
System component traces record the latency of and relationships between operations in the cluster.

Kubernetes components emit traces using the OpenTelemetry Protocol with the gRPC exporter and can be collected and routed to tracing backends using an OpenTelemetry Collector.

Trace Collection
Kubernetes components have built-in gRPC exporters for OTLP to export traces, either with an OpenTelemetry Collector, or without an OpenTelemetry Collector.

For a complete guide to collecting traces and using the collector, see Getting Started with the OpenTelemetry Collector. However, there are a few things to note that are specific to Kubernetes components.

By default, Kubernetes components export traces using the grpc exporter for OTLP on the IANA OpenTelemetry port, 4317. As an example, if the collector is running as a sidecar to a Kubernetes component, the following receiver configuration will collect spans and log them to standard output:

receivers:
  otlp:
    protocols:
      grpc:
exporters:
  # Replace this exporter with the exporter for your backend
  exporters:
    debug:
      verbosity: detailed
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
To directly emit traces to a backend without utilizing a collector, specify the endpoint field in the Kubernetes tracing configuration file with the desired trace backend address. This method negates the need for a collector and simplifies the overall structure.

For trace backend header configuration, including authentication details, environment variables can be used with OTEL_EXPORTER_OTLP_HEADERS, see OTLP Exporter Configuration.

Additionally, for trace resource attribute configuration such as Kubernetes cluster name, namespace, Pod name, etc., environment variables can also be used with OTEL_RESOURCE_ATTRIBUTES, see OTLP Kubernetes Resource.

Component traces
kube-apiserver traces
The kube-apiserver generates spans for incoming HTTP requests, and for outgoing requests to webhooks, etcd, and re-entrant requests. It propagates the W3C Trace Context with outgoing requests but does not make use of the trace context attached to incoming requests, as the kube-apiserver is often a public endpoint.

Enabling tracing in the kube-apiserver
To enable tracing, provide the kube-apiserver with a tracing configuration file with --tracing-config-file=<path-to-config>. This is an example config that records spans for 1 in 10000 requests, and uses the default OpenTelemetry endpoint:

apiVersion: apiserver.config.k8s.io/v1
kind: TracingConfiguration
# default value
#endpoint: localhost:4317
samplingRatePerMillion: 100
For more information about the TracingConfiguration struct, see API server config API (v1).

kubelet traces
FEATURE STATE: Kubernetes v1.34 [stable](enabled by default)
The kubelet CRI interface and authenticated http servers are instrumented to generate trace spans. As with the apiserver, the endpoint and sampling rate are configurable. Trace context propagation is also configured. A parent span's sampling decision is always respected. A provided tracing configuration sampling rate will apply to spans without a parent. Enabled without a configured endpoint, the default OpenTelemetry Collector receiver address of "localhost:4317" is set.

Enabling tracing in the kubelet
To enable tracing, apply the tracing configuration. This is an example snippet of a kubelet config that records spans for 1 in 10000 requests, and uses the default OpenTelemetry endpoint:

apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
tracing:
  # default value
  #endpoint: localhost:4317
  samplingRatePerMillion: 100
If the samplingRatePerMillion is set to one million (1000000), then every span will be sent to the exporter.

The kubelet in Kubernetes v1.36 collects spans from the garbage collection, pod synchronization routine as well as every gRPC method. The kubelet propagates trace context with gRPC requests so that container runtimes with trace instrumentation, such as CRI-O and containerd, can associate their exported spans with the trace context from the kubelet. The resulting traces will have parent-child links between kubelet and container runtime spans, providing helpful context when debugging node issues.

Please note that exporting spans always comes with a small performance overhead on the networking and CPU side, depending on the overall configuration of the system. If there is any issue like that in a cluster which is running with tracing enabled, then mitigate the problem by either reducing the samplingRatePerMillion or disabling tracing completely by removing the configuration.

Stability
Tracing instrumentation is still under active development, and may change in a variety of ways. This includes span names, attached attributes, instrumented endpoints, etc. Until this feature graduates to stable, there are no guarantees of backwards compatibility for tracing instrumentation

System Logs
System component logs record events happening in cluster, which can be very useful for debugging. You can configure log verbosity to see more or less detail. Logs can be as coarse-grained as showing errors within a component, or as fine-grained as showing step-by-step traces of events (like HTTP access logs, pod state changes, controller actions, or scheduler decisions).

Warning:
In contrast to the command line flags described here, the log output itself does not fall under the Kubernetes API stability guarantees: individual log entries and their formatting may change from one release to the next!
Klog
klog is the Kubernetes logging library. klog generates log messages for the Kubernetes system components.

Kubernetes is in the process of simplifying logging in its components. The following klog command line flags are deprecated starting with Kubernetes v1.23 and removed in Kubernetes v1.26:

--add-dir-header
--alsologtostderr
--log-backtrace-at
--log-dir
--log-file
--log-file-max-size
--logtostderr
--one-output
--skip-headers
--skip-log-headers
--stderrthreshold
Output will always be written to stderr, regardless of the output format. Output redirection is expected to be handled by the component which invokes a Kubernetes component. This can be a POSIX shell or a tool like systemd.

In some cases, for example a distroless container or a Windows system service, those options are not available. Then the kube-log-runner binary can be used as wrapper around a Kubernetes component to redirect output. A prebuilt binary is included in several Kubernetes base images under its traditional name as /go-runner and as kube-log-runner in server and node release archives.

This table shows how kube-log-runner invocations correspond to shell redirection:

Usage	POSIX shell (such as bash)	kube-log-runner <options> <cmd>
Merge stderr and stdout, write to stdout	2>&1	kube-log-runner (default behavior)
Redirect both into log file	1>>/tmp/log 2>&1	kube-log-runner -log-file=/tmp/log
Copy into log file and to stdout	2>&1 | tee -a /tmp/log	kube-log-runner -log-file=/tmp/log -also-stdout
Redirect only stdout into log file	>/tmp/log	kube-log-runner -log-file=/tmp/log -redirect-stderr=false
Klog output
An example of the traditional klog native format:

I1025 00:15:15.525108       1 httplog.go:79] GET /api/v1/namespaces/kube-system/pods/metrics-server-v0.3.1-57c75779f-9p8wg: (1.512ms) 200 [pod_nanny/v0.0.0 (linux/amd64) kubernetes/$Format 10.56.1.19:51756]
The message string may contain line breaks:

I1025 00:15:15.525108       1 example.go:79] This is a message
which has a line break.
Structured Logging
FEATURE STATE: Kubernetes v1.23 [beta]
Warning:
Migration to structured log messages is an ongoing process. Not all log messages are structured in this version. When parsing log files, you must also handle unstructured log messages.

Log formatting and value serialization are subject to change.

Structured logging introduces a uniform structure in log messages allowing for programmatic extraction of information. You can store and process structured logs with less effort and cost. The code which generates a log message determines whether it uses the traditional unstructured klog output or structured logging.

The default formatting of structured log messages is as text, with a format that is backward compatible with traditional klog:

<klog header> "<message>" <key1>="<value1>" <key2>="<value2>" ...
Example:

I1025 00:15:15.525108       1 controller_utils.go:116] "Pod status updated" pod="kube-system/kubedns" status="ready"
Strings are quoted. Other values are formatted with %+v, which may cause log messages to continue on the next line depending on the data.

I1025 00:15:15.525108       1 example.go:116] "Example" data="This is text with a line break\nand \"quotation marks\"." someInt=1 someFloat=0.1 someStruct={StringField: First line,
second line.}
Contextual Logging
FEATURE STATE: Kubernetes v1.30 [beta]
Contextual logging builds on top of structured logging. It is primarily about how developers use logging calls: code based on that concept is more flexible and supports additional use cases as described in the Contextual Logging KEP.

If developers use additional functions like WithValues or WithName in their components, then log entries contain additional information that gets passed into functions by their caller.

For Kubernetes 1.36, this is gated behind the ContextualLogging feature gate and is enabled by default. The infrastructure for this was added in 1.24 without modifying components. The component-base/logs/example command demonstrates how to use the new logging calls and how a component behaves that supports contextual logging.

$ cd $GOPATH/src/k8s.io/kubernetes/staging/src/k8s.io/component-base/logs/example/cmd/
$ go run . --help
...
      --feature-gates mapStringBool  A set of key=value pairs that describe feature gates for alpha/experimental features. Options are:
                                     AllAlpha=true|false (ALPHA - default=false)
                                     AllBeta=true|false (BETA - default=false)
                                     ContextualLogging=true|false (BETA - default=true)
$ go run . --feature-gates ContextualLogging=true
...
I0222 15:13:31.645988  197901 example.go:54] "runtime" logger="example.myname" foo="bar" duration="1m0s"
I0222 15:13:31.646007  197901 example.go:55] "another runtime" logger="example" foo="bar" duration="1h0m0s" duration="1m0s"
The logger key and foo="bar" were added by the caller of the function which logs the runtime message and duration="1m0s" value, without having to modify that function.

With contextual logging disable, WithValues and WithName do nothing and log calls go through the global klog logger. Therefore this additional information is not in the log output anymore:

$ go run . --feature-gates ContextualLogging=false
...
I0222 15:14:40.497333  198174 example.go:54] "runtime" duration="1m0s"
I0222 15:14:40.497346  198174 example.go:55] "another runtime" duration="1h0m0s" duration="1m0s"
JSON log format
FEATURE STATE: Kubernetes v1.19 [alpha]
Warning:
JSON output does not support many standard klog flags. For list of unsupported klog flags, see the Command line tool reference.

Not all logs are guaranteed to be written in JSON format (for example, during process start). If you intend to parse logs, make sure you can handle log lines that are not JSON as well.

Field names and JSON serialization are subject to change.

The --logging-format=json flag changes the format of logs from klog native format to JSON format. Example of JSON log format (pretty printed):

{
   "ts": 1580306777.04728,
   "v": 4,
   "msg": "Pod status updated",
   "pod":{
      "name": "nginx-1",
      "namespace": "default"
   },
   "status": "ready"
}
Keys with special meaning:

ts - timestamp as Unix time (required, float)
v - verbosity (only for info and not for error messages, int)
err - error string (optional, string)
msg - message (required, string)
List of components currently supporting JSON format:

kube-controller-manager
kube-apiserver
kube-scheduler
kubelet
Log verbosity level
The -v flag controls log verbosity. Increasing the value increases the number of logged events. Decreasing the value decreases the number of logged events. Increasing verbosity settings logs increasingly less severe events. A verbosity setting of 0 logs only critical events.

Log location
There are two types of system components: those that run in a container and those that do not run in a container. For example:

The Kubernetes scheduler and kube-proxy run in a container.
The kubelet and container runtime do not run in containers.
On machines with systemd, the kubelet and container runtime write to journald. Otherwise, they write to .log files in the /var/log directory. System components inside containers always write to .log files in the /var/log directory, bypassing the default logging mechanism. Similar to the container logs, you should rotate system component logs in the /var/log directory. In Kubernetes clusters created by the kube-up.sh script, log rotation is configured by the logrotate tool. The logrotate tool rotates logs daily, or once the log size is greater than 100MB.

Log query
FEATURE STATE: Kubernetes v1.36 [stable](enabled by default)
The Log Query feature can help debugging issues in both Linux and Windows nodes. Introduced in Kubernetes v1.27, the feature allows viewing logs of services running on the node. To use the feature, ensure that the kubelet configuration options enableSystemLogHandler and enableSystemLogQuery are both set to true for the target node.

In Kubernetes v1.36 this feature graduated to stable and the NodeLogQueryfeature gate is now locked to true, hence the feature gate is enabled by default, leaving enableSystemLogHandler as the only option required to enable or disable the Log Query feature.

enableSystemLogHandler defaults to false and is recommended to be left disabled unless actively debugging.

Warning:
Granting permissions to nodes/proxy (even just get permission) also authorizes access to powerful kubelet APIs that can be used to execute commands in any container running on the node, so be careful about how you manage them. See Kubelet authentication/authorization for more information.
On Linux, the assumption is that service logs are available via journald. On Windows the assumption is that service logs are available in the application log provider. On both operating systems, logs are also available by reading files within /var/log/.

Provided you are authorized to interact with node objects, you can try out this feature on all your nodes or just a subset. Here is an example to retrieve the kubelet service logs from a node:

# Fetch kubelet logs from a node named node-1.example
kubectl get --raw "/api/v1/nodes/node-1.example/proxy/logs/?query=kubelet"
You can also fetch files, provided that the files are in a directory that the kubelet allows for log fetches. For example, you can fetch a log from /var/log on a Linux node:

kubectl get --raw "/api/v1/nodes/<insert-node-name-here>/proxy/logs/?query=/<insert-log-file-name-here>"
The kubelet uses heuristics to retrieve logs. This helps if you are not aware whether a given system service is writing logs to the operating system's native logger like journald or to a log file in /var/log/. The heuristics first checks the native logger and if that is not available attempts to retrieve the first logs from /var/log/<servicename> or /var/log/<servicename>.log or /var/log/<servicename>/<servicename>.log.

The complete list of options that can be used are:

Option	Description
boot	boot show messages from a specific system boot
pattern	pattern filters log entries by the provided PERL-compatible regular expression
query	query specifies services(s) or files from which to return logs (required)
sinceTime	an RFC3339 timestamp from which to show logs (inclusive)
untilTime	an RFC3339 timestamp until which to show logs (inclusive)
tailLines	specify how many lines from the end of the log to retrieve; the default is to fetch the whole log
Example of a more complex query:

# Fetch kubelet logs from a node named node-1.example that have the word "error"
kubectl get --raw "/api/v1/nodes/node-1.example/proxy/logs/?query=kubelet&pattern=error"

Kubernetes has become the de-facto industry standard for container orchestration. It provides the required abstraction for efficiently managing large-scale containerized applications with declarative configurations, an easy deployment mechanism, and both scaling and self-healing capabilities.

As with any system, logs help engineers gain observability into containers and the Kubernetes clusters they’re running on and the key role they play is evident in a lot of incidents featuring Kubernetes failures.  Yet Kubernetes poses a set of unique logging challenges.

Kubernetes is a highly distributed and dynamic environment. In production, you’ll most likely be running dozens of machines with hundreds of containers that can be terminated, restarted, or rescheduled at any point in time. This transient and dynamic nature of the system is a challenge in itself.

Kubernetes clusters also consist of multiple layers that need monitoring, each producing different types of logs.

Worried? Don’t be. Thankfully, there is a lot of literature available on how to gain visibility into Kubernetes. There are also various logging tools that integrate natively with Kubernetes to make the task easier. In this article, we’ll review some of these tools as well as review the Kubernetes logging architecture.

A Simple Example: Containerized application logging with Kubelet
Logging to stdout and stderr standard output streams
The first layer of logs that can be collected from a Kubernetes cluster are those being generated by your containerized applications. The best practice is to write your application logs to the standard output (stdout) and standard error (stderr) streams. You shouldn’t worry about losing these logs, as kubelet, Kubernetes’ node agent, will collect these streams and write them to a local file behind the scenes, so you can access them with Kubernetes.

Let’s take a look at an example pod manifest that will result in running one container logging to stdout:

apiVersion: v1
kind: Pod
metadata:
  name: example
spec:
  containers:
  - name: example
    image: busybox
    args: [/bin/sh, -c, 'while true; do echo $(date); sleep 1; done']
Copy

To apply the manifest, run:

kubectl apply -f example.yaml
Copy

To take a look at the logs for this container:

kubectl logs example
Copy

The command calls kubelet service on that node to retrieve the logs. As you can see, the logs are collected and presented with Kubernetes. This is done for each container in a pod, across your cluster. Using kubectl for retrieving logs saves you from needing to access individual nodes in the cluster.

Kubectl can only show a single pod’s logs at a time. If you need to aggregate many pods into a single stream, you would need to use kubetail command, or higher level log aggregation and management tools that we will discuss later in this article.

Using a sidecar for logging
If your application does not output to stdout and stderr, then you can deploy a sidecar container alongside your application that will pick up the application logs and stream them to stdout and stderr respectively.

Such a sidecar pattern enables also performing some log manipulations, such as aggregating several log streams on the node into one, or separating one application log stream into several logical streams (each handled by a dedicated sidecar instance).

For persisting container logs, the common approach is to write logs to a log file and then use a sidecar container:

apiVersion: v1
kind: Pod
metadata:
name: example
spec:
containers:
- name: example
image: busybox
args:
- /bin/sh
- -c
- >
while true;
do
echo "$(date)\n" >> /var/log/example.log;
sleep 1;
done
volumeMounts:
- name: varlog
mountPath: /var/log
- name: sidecar
image: busybox
args: [/bin/sh, -c, 'tail -f /var/log/example.log']
volumeMounts:
- name: varlog
mountPath: /var/log
volumes:
- name: varlog
emptyDir: {}
As seen in the pod configuration above, a sidecar container will run in the same pod along with the application container, mounting the same volume and processing the logs separately.

Kubernetes logging architecture
As mentioned, one main challenge with logging Kubernetes is understanding what logs are generated and how to use them. In the following sections I will look into the node logging and the cluster logging.

Kubernetes Node logging
When a container running on Kubernetes writes its logs to stdout or stderr streams, they are picked up by the kubelet service running on that node, and are delegated to the container engine for handling based on the logging driver configured in Kubernetes.

In most cases, Docker container logs will end up in the /var/log/containers directory on your host. Docker supports multiple logging drivers but, unfortunately, Kubernetes API does not support driver configuration.

Once a container terminates or restarts, kubelet keeps its logs on the node. To prevent these files from consuming all of the host’s storage, a log rotation mechanism should be set on the node.

Kubernetes doesn’t provide built-in log rotation, but this functionality is available in many tools, such as Docker’s log-opt, or standard file shippers or even a simple custom cron job. When a container is evicted from the node, so are its corresponding log files.

Depending on what operating system and additional services you’re running on your host machine, you may need to take a look at additional logs. For example, in Linux journald logs can be retrieved using the journalctl command:

$ journalctl -u docker

-- Logs begin at Wed 2019-05-29 10:59:24 CEST, end at Mon 2019-07-15 10:55:17 CEST. --

jul 29 10:59:35 thinkpad systemd[1]: Starting Docker Application Container Engine...

jul 29 10:59:35 thinkpad dockerd[2172]: time="2019-05-29T10:59:35.285765854+02:00" level=info msg="libcontainerd: started new docker-containerd process" p

jul 29 10:59:35 thinkpad dockerd[2172]: time="2019-05-29T10:59:35.286021587+02:00" level=info msg="parsed scheme: \"unix\"" module=grpc
As you can see in the above example, Docker container runtime writes its logs to journald. Other important Kubernetes system processes at the node level are kubelet, which also logs to journald, and kube-proxy, the network proxy that runs on each node, which logs to /var/log directory.

Logging kernel events might also be required in some scenarios. You might, for example, use Unix dmesg command to print the message buffer of the kernel to debug device drivers issues:

$ dmesg

[ 0.000000] microcode: microcode updated early to revision 0xb4, date = 2019-04-01

[ 0.000000] Linux version 4.15.0-54-generic (buildd@lgw01-amd64-014) (gcc version 7.4.0 (Ubuntu 7.4.0-1ubuntu1~18.04.1)) #58-Ubuntu SMP Mon Jun 24 10:55:24 UTC 2019 (Ubuntu 4.15.0-54.58-generic 4.15.18)

[ 0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz-4.15.0-54-generic root=UUID=6e228d30-6415-4b41-b992-172d6899693e ro quiet splash vt.handoff=1

[ 0.000000] KERNEL supported cpus:

[ 0.000000] Intel GenuineIntel

[ 0.000000] AMD AuthenticAMD

[ 0.000000] Centaur CentaurHauls

[ 0.000000] x86/fpu: Supporting XSAVE feature 0x001: 'x87 floating point registers'

[ 0.000000] x86/fpu: Supporting XSAVE feature 0x002: 'SSE registers'

[ 0.000000] x86/fpu: Supporting XSAVE feature 0x004: 'AVX registers'

[ 0.000000] x86/fpu: Supporting XSAVE feature 0x008: 'MPX bounds registers'

[ 0.000000] x86/fpu: Supporting XSAVE feature 0x010: 'MPX CSR'
Kubernetes system components logging
In addition to kubelet and kube-proxy node services we covered earlier, there are control plane components on the level of the Kubernetes cluster itself that can be logged, as well as additional data types that can be used (events, audit logs). Together, these different types of data can give you visibility into how Kubernetes is performing as a system.

The following are the main system components of Kubernetes control plane:

kube-apiserver – the API server serving as the access point to the cluster
kube-scheduler – the element that determines where to run containers
etcd – the key-value store used as Kubernetes’ cluster configuration storage
Some of these components run in a container, and some of them run on the operating system level (in most cases, a systemd service).

The systemd services write to journald, and components running in containers write logs to the /var/log directory, unless the container engine has been configured to stream logs differently.

Kubernetes’ system components use Kubernetes’ logging library — klog — to generate their log messages. These system logs were not known to follow uniform structure, which made it difficult to parse, query and analyze. However, Kubernetes’ recent v1.19 release introduced a new option in klog for structured logging in text as well as in JSON format.

Structured logging provides a well-defined structure in klog native format, with a list of key-value pairs for the variant payload. Using the --logging-format=json flag enables JSON output.

It’s important to note that structured logging (both string and JSON options) is still in alpha per v1.19, with incremental adoption, so you may encounter early stage issues such as system logs that are still unstructured, log formatting changes, or klog flags which are supported for JSON. Check the documentation for updated feature status and information here.

Kubernetes events
Kubernetes events can indicate any Kubernetes resource state changes and errors, such as exceeded resource quota or pending pods, as well as any informational messages.

The command kubectl get events -n <namespace> returns all events within a specific namespace:

LAST SEEN   TYPE      REASON                  OBJECT                                  MESSAGE

4m22s       Normal    ExternalProvisioning    persistentvolumeclaim/mysql-pv-claim    waiting for a volume to be created, either by external provisioner "docker.io/hostpath" or manually created by system administrator

4m22s       Normal    Provisioning            persistentvolumeclaim/mysql-pv-claim    External provisioner is provisioning volume for claim "default/mysql-pv-claim"

4m22s       Normal    ProvisioningSucceeded   persistentvolumeclaim/mysql-pv-claim    Successfully provisioned volume pvc-b5419197-f122-4263-9c78-e9fb457db630

4m22s       Warning   FailedScheduling        pod/wordpress-57b89f8b5b-gt6bv          pod has unbound immediate PersistentVolumeClaims

4m20s       Normal    Scheduled               pod/wordpress-57b89f8b5b-gt6bv          Successfully assigned default/wordpress-57b89f8b5b-gt6bv to docker-desktop

4m18s       Normal    Pulled                  pod/wordpress-57b89f8b5b-gt6bv          Container image "wordpress:4.8-apache" already present on machine

4m18s       Normal    Created                 pod/wordpress-57b89f8b5b-gt6bv          Created container wordpress

4m18s       Normal    Started                 pod/wordpress-57b89f8b5b-gt6bv          Started container wordpress

4m22s       Normal    SuccessfulCreate        replicaset/wordpress-57b89f8b5b         Created pod: wordpress-57b89f8b5b-gt6bv
Using kubectl describe pod <pod-name> provides a lot of useful information about the pod, including a section listing the latest events:

Events:

Type     Reason            Age                    From                     Message

----     ------            ----                   ----                     -------

Warning  FailedScheduling  9m44s                  default-scheduler        persistentvolumeclaim "mysql-pv-claim" not found

Warning  FailedScheduling  9m44s (x2 over 9m44s)  default-scheduler        pod has unbound immediate PersistentVolumeClaims

Normal   Scheduled         9m42s                  default-scheduler        Successfully assigned default/wordpress-mysql-694777bb76-tqn55 to docker-desktop

Normal   Pulled            9m40s                  kubelet, docker-desktop  Container image "mysql:5.6" already present on machine

Normal   Created           9m40s                  kubelet, docker-desktop  Created container mysql

Normal   Started           9m40s                  kubelet, docker-desktop  Started container mysql
Kubernetes audit logs
Audit logs can be useful for compliance as they should help you answer the questions of what happened, who did what and when.

Kubernetes provides flexible auditing of kube-apiserver requests based on policies. These help you track all activities in chronological order.

Here is an example of an audit log:

{
  "kind":"Event",
  "apiVersion":"audit.k8s.io/v1beta1",
  "metadata":{ "creationTimestamp":"2019-08-22T12:00:00Z" },
  "level":"Metadata",
  "timestamp":"2019-08-22T12:00:00Z",
  "auditID":"23bc44ds-2452-242g-fsf2-4242fe3ggfes",
  "stage":"RequestReceived",
  "requestURI":"/api/v1/namespaces/default/persistentvolumeclaims",
  "verb":"list",
  "user": {
  "username":"user@example.org",
  "groups":[ "system:authenticated" ]
  },
  "sourceIPs":[ "172.12.56.1" ],
  "objectRef": {
  "resource":"persistentvolumeclaims",
  "namespace":"default",
  "apiVersion":"v1"
  },
  "requestReceivedTimestamp":"2019-08-22T12:00:00Z",
  "stageTimestamp":"2019-08-22T12:00:00Z"
}
For more information on monitoring Kubernetes logs for anomalies, as well as for threat detection, check out this post.

Kubernetes logging tools
Hopefully, you’ve now got a better understanding of the different logging layers and log types available in Kubernetes. The logging tools reviewed in this section play an important role in putting all of this together to build a Kubernetes logging pipeline.

Kubernetes doesn’t provide log aggregation of its own. However, Kubernetes release contains optional logging agents for Elasticsearch and for Stackdriver Logging (for use with Google Cloud Platform), and Fluentd as node agent. In the following sections I’ll look into each of them.

The general architecture for cluster log aggregation is to have a local agent (such as Fluentd or Filebeat which are discussed below) to gather the data and send it to the central log management. The agent usually deploys per node as a DaemonSet to collect all the logs on that node. However, it can also deploy per pod for finer granularity. The agent can also perform some filtering and manipulation of the logs before sending them, to improve the logs ingestion and analysis or to reduce log volume. I highly recommend adding metadata from the node (which is accessible to the local logging agent), such as pod name, cluster id and region, which greatly helps in analysis and troubleshooting.

Fluentd
Fluentd is a popular open-source log aggregator that allows you to collect various logs from your Kubernetes cluster, process them, and then ship them to a data storage backend of your choice.

Kubernetes-native, fluentd integrates seamlessly with Kubernetes deployments.  The most common method for deploying fluentd is as a daemonset which ensures a fluentd pod runs on each pod. Similar to other log forwarders and aggregators, fluentd appends useful metadata fields to logs such as the pod name and Kubernetes namespace, which helps provide more context.

ELK Stack
The ELK Stack (Elasticsearch, Logstash and Kibana) is another very popular open-source tool used for logging Kubernetes, and is actually comprised of four components:

Elasticsearch – provides a scalable, RESTful search and analytics engine for storing Kubernetes logs
Kibana – the visualization layer, allowing you with a user interface to query and visualize logs
Logstash – the log aggregator used to collect and process the logs before sending them into Elasticsearch
Beats – Filebeat and Metricbeat are ELK-native lightweight data shippers used for shipping log files and metrics into Elasticsearch
ELK can be deployed on Kubernetes as well, on-prem or in the cloud. While Beats is Elasticsearch’s native shipper, a common alternative for Kubernetes installations is to use Fluentd to send logs to Elasticsearch (sometimes referred to as the EFK stack).

Together, these components provide Kubernetes users with an end-to-end logging solution. As effective as it is, deploying and managing ELK deployments at scale is a challenge unto itself.

Logz.io offers users with a fully-managed option for using the stack to log Kubernetes, with built-in integrations and monitoring dashboards. Get more information on logging Kubernetes with Logz.io.

Google Stackdriver
And last but not least…Google Stackdriver.

Stackdriver is another Kubernetes-native logging tool that provides users with a centralized logging solution. If you’re using GKE, Stackdriver can be easily enabled using the following command:

gcloud container clusters create [CLUSTER_NAME] \
 --zone [ZONE]
 --project-id [PROJECT_ID]
 --enable-stackdriver-kubernetes \
 --cluster-version=latest
For more information on using Stackdriver to log Kubernetes, check out Logging Using Stackdriver.

Endnotes
Once a cluster is up and running with logging in place, you can make sure your workloads and underlying infrastructure stay healthy. Logging also helps you to be prepared for issues that may arise during the deployment of a new production release and stop them before they affect the customer’s experience.

Kubernetes’ kubectl and kubetail commands can provide a useful manual way to inspect logs, but monitoring clusters in production calls for a cluster-wide log aggregation and analysis tool such as ELK stack. In production it’s recommended to keep your logs separately from the Kubernetes cluster running your monitored application, so that your logs remain accessible for troubleshooting even (and especially) during cluster outage and issues.

It takes time to implement production-ready logging for your services, as well as to set up alerts and tune them appropriately. However, an effective logging solution allows you to focus on monitoring your key business metrics, which, in turn, increases the reliability of your products and your company’s revenue.

To learn more contact us or visit our blog.

kubectl logs and other useful kubectl commands
Some useful kubectl commands are listed below:

kubectl logs -f # stream logs
kubectl logs --since=1h # return logs newer than a relative duration
kubectl logs --since-time=2020-08-13T10:46:00.000000000Z # return logs after a specific date (RFC3339)
kubectl logs --previous # print the logs for the previous instance of the container
kubectl logs -c # print the logs of this container
kubectl logs -l #  print logs from all containers in pods defined by label
kubectl get events --sort-by=’.metadata.creationTimestamp’ # print all events in chronological order
kubectl describe pod  # print pod details like status or recent events

Logging Architecture
Application logs can help you understand what is happening inside your application. The logs are particularly useful for debugging problems and monitoring cluster activity. Most modern applications have some kind of logging mechanism. Likewise, container engines are designed to support logging. The easiest and most adopted logging method for containerized applications is writing to standard output and standard error streams.

However, the native functionality provided by a container engine or runtime is usually not enough for a complete logging solution.

For example, you may want to access your application's logs if a container crashes, a pod gets evicted, or a node dies.

In a cluster, logs should have a separate storage and lifecycle independent of nodes, pods, or containers. This concept is called cluster-level logging.

Cluster-level logging architectures require a separate backend to store, analyze, and query logs. Kubernetes does not provide a native storage solution for log data. Instead, there are many logging solutions that integrate with Kubernetes. The following sections describe how to handle and store logs on nodes.

Pod and container logs
Kubernetes captures logs from each container in a running Pod.

This example uses a manifest for a Pod with a container that writes text to the standard output stream, once per second.

debug/counter-pod.yaml
Copy debug/counter-pod.yaml to clipboard
apiVersion: v1
kind: Pod
metadata:
  name: counter
spec:
  containers:
  - name: count
    image: busybox:1.28
    args: [/bin/sh, -c,
            'i=0; while true; do echo "$i: $(date)"; i=$((i+1)); sleep 1; done']
To run this pod, use the following command:

kubectl apply -f https://k8s.io/examples/debug/counter-pod.yaml
The output is:

pod/counter created
To fetch the logs, use the kubectl logs command, as follows:

kubectl logs counter
The output is similar to:

0: Fri Apr  1 11:42:23 UTC 2022
1: Fri Apr  1 11:42:24 UTC 2022
2: Fri Apr  1 11:42:25 UTC 2022
You can use kubectl logs --previous to retrieve logs from a previous instantiation of a container. If your pod has multiple containers, specify which container's logs you want to access by appending a container name to the command, with a -c flag, like so:

kubectl logs counter -c count
Container log streams
FEATURE STATE: Kubernetes v1.32 [alpha](disabled by default)
As an alpha feature, the kubelet can split out the logs from the two standard streams produced by a container: standard output and standard error. To use this behavior, you must enable the PodLogsQuerySplitStreams feature gate. With that feature gate enabled, Kubernetes 1.36 allows access to these log streams directly via the Pod API. You can fetch a specific stream by specifying the stream name (either Stdout or Stderr), using the stream query string. You must have access to read the log subresource of that Pod.

To demonstrate this feature, you can create a Pod that periodically writes text to both the standard output and error stream.

debug/counter-pod-err.yaml
Copy debug/counter-pod-err.yaml to clipboard
apiVersion: v1
kind: Pod
metadata:
  name: counter-err
spec:
  containers:
  - name: count
    image: busybox:1.28
    args: [/bin/sh, -c,
            'i=0; while true; do echo "$i: $(date)"; echo "$i: err" >&2 ; i=$((i+1)); sleep 1; done']
To run this pod, use the following command:

kubectl apply -f https://k8s.io/examples/debug/counter-pod-err.yaml
To fetch only the stderr log stream, you can run:

kubectl get --raw "/api/v1/namespaces/default/pods/counter-err/log?stream=Stderr"
See the kubectl logs documentation for more details.

How nodes handle container logs
Node level logging

A container runtime handles and redirects any output generated to a containerized application's stdout and stderr streams. Different container runtimes implement this in different ways; however, the integration with the kubelet is standardized as the CRI logging format.

By default, if a container restarts, the kubelet keeps one terminated container with its logs. If a pod is evicted from the node, all corresponding containers are also evicted, along with their logs.

The kubelet makes logs available to clients via a special feature of the Kubernetes API. The usual way to access this is by running kubectl logs.

Log rotation
FEATURE STATE: Kubernetes v1.21 [stable]
The kubelet is responsible for rotating container logs and managing the logging directory structure. The kubelet sends this information to the container runtime (using CRI), and the runtime writes the container logs to the given location.

You can configure two kubelet configuration settings, containerLogMaxSize (default 10Mi) and containerLogMaxFiles (default 5), using the kubelet configuration file. These settings let you configure the maximum size for each log file and the maximum number of files allowed for each container respectively.

In order to perform an efficient log rotation in clusters where the volume of the logs generated by the workload is large, kubelet also provides a mechanism to tune how the logs are rotated in terms of how many concurrent log rotations can be performed and the interval at which the logs are monitored and rotated as required. You can configure two kubelet configuration settings, containerLogMaxWorkers and containerLogMonitorInterval using the kubelet configuration file.

When you run kubectl logs as in the basic logging example, the kubelet on the node handles the request and reads directly from the log file. The kubelet returns the content of the log file.

Note:
Only the contents of the latest log file are available through kubectl logs.

For example, if a Pod writes 40 MiB of logs and the kubelet rotates logs after 10 MiB, running kubectl logs returns at most 10MiB of data.

System component logs
There are two types of system components: those that typically run in a container, and those components directly involved in running containers. For example:

The kubelet and container runtime do not run in containers. The kubelet runs your containers (grouped together in pods)
The Kubernetes scheduler, controller manager, and API server run within pods (usually static Pods). The etcd component runs in the control plane, and most commonly also as a static pod. If your cluster uses kube-proxy, you typically run this as a DaemonSet.
Log locations
The way that the kubelet and container runtime write logs depends on the operating system that the node uses:

Linux
Windows
On Linux nodes that use systemd, the kubelet and container runtime write to journald by default. You use journalctl to read the systemd journal; for example: journalctl -u kubelet.

If systemd is not present, the kubelet and container runtime write to .log files in the /var/log directory. If you want to have logs written elsewhere, you can indirectly run the kubelet via a helper tool, kube-log-runner, and use that tool to redirect kubelet logs to a directory that you choose.

By default, kubelet directs your container runtime to write logs into directories within /var/log/pods.

For more information on kube-log-runner, read System Logs.



For Kubernetes cluster components that run in pods, these write to files inside the /var/log directory, bypassing the default logging mechanism (the components do not write to the systemd journal). You can use Kubernetes' storage mechanisms to map persistent storage into the container that runs the component.

Kubelet allows changing the pod logs directory from default /var/log/pods to a custom path. This adjustment can be made by configuring the podLogsDir parameter in the kubelet's configuration file.

Caution:
It's important to note that the default location /var/log/pods has been in use for an extended period and certain processes might implicitly assume this path. Therefore, altering this parameter must be approached with caution and at your own risk.

Another caveat to keep in mind is that the kubelet supports the location being on the same disk as /var. Otherwise, if the logs are on a separate filesystem from /var, then the kubelet will not track that filesystem's usage, potentially leading to issues if it fills up.

For details about etcd and its logs, view the etcd documentation. Again, you can use Kubernetes' storage mechanisms to map persistent storage into the container that runs the component.

Note:
If you deploy Kubernetes cluster components (such as the scheduler) to log to a volume shared from the parent node, you need to consider and ensure that those logs are rotated. Kubernetes does not manage that log rotation.

Your operating system may automatically implement some log rotation - for example, if you share the directory /var/log into a static Pod for a component, node-level log rotation treats a file in that directory the same as a file written by any component outside Kubernetes.

Some deploy tools account for that log rotation and automate it; others leave this as your responsibility.

Cluster-level logging architectures
While Kubernetes does not provide a native solution for cluster-level logging, there are several common approaches you can consider. Here are some options:

Use a node-level logging agent that runs on every node.
Include a dedicated sidecar container for logging in an application pod.
Push logs directly to a backend from within an application.
Using a node logging agent
Using a node level logging agent

You can implement cluster-level logging by including a node-level logging agent on each node. The logging agent is a dedicated tool that exposes logs or pushes logs to a backend. Commonly, the logging agent is a container that has access to a directory with log files from all of the application containers on that node.

Because the logging agent must run on every node, it is recommended to run the agent as a DaemonSet.

Node-level logging creates only one agent per node and doesn't require any changes to the applications running on the node.

Containers write to stdout and stderr, but with no agreed format. A node-level agent collects these logs and forwards them for aggregation.

Using a sidecar container with the logging agent
You can use a sidecar container in one of the following ways:

The sidecar container streams application logs to its own stdout.
The sidecar container runs a logging agent, which is configured to pick up logs from an application container.
Streaming sidecar container
Sidecar container with a streaming container

By having your sidecar containers write to their own stdout and stderr streams, you can take advantage of the kubelet and the logging agent that already run on each node. The sidecar containers read logs from a file, a socket, or journald. Each sidecar container prints a log to its own stdout or stderr stream.

This approach allows you to separate several log streams from different parts of your application, some of which can lack support for writing to stdout or stderr. The logic behind redirecting logs is minimal, so it's not a significant overhead. Additionally, because stdout and stderr are handled by the kubelet, you can use built-in tools like kubectl logs.

For example, a pod runs a single container, and the container writes to two different log files using two different formats. Here's a manifest for the Pod:

admin/logging/two-files-counter-pod.yaml
Copy admin/logging/two-files-counter-pod.yaml to clipboard
apiVersion: v1
kind: Pod
metadata:
  name: counter
spec:
  containers:
  - name: count
    image: busybox:1.28
    args:
    - /bin/sh
    - -c
    - >
      i=0;
      while true;
      do
        echo "$i: $(date)" >> /var/log/1.log;
        echo "$(date) INFO $i" >> /var/log/2.log;
        i=$((i+1));
        sleep 1;
      done
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  volumes:
  - name: varlog
    emptyDir: {}
It is not recommended to write log entries with different formats to the same log stream, even if you managed to redirect both components to the stdout stream of the container. Instead, you can create two sidecar containers. Each sidecar container could tail a particular log file from a shared volume and then redirect the logs to its own stdout stream.

Here's a manifest for a pod that has two sidecar containers:

admin/logging/two-files-counter-pod-streaming-sidecar.yaml
Copy admin/logging/two-files-counter-pod-streaming-sidecar.yaml to clipboard
apiVersion: v1
kind: Pod
metadata:
  name: counter
spec:
  containers:
  - name: count
    image: busybox:1.28
    args:
    - /bin/sh
    - -c
    - >
      i=0;
      while true;
      do
        echo "$i: $(date)" >> /var/log/1.log;
        echo "$(date) INFO $i" >> /var/log/2.log;
        i=$((i+1));
        sleep 1;
      done
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  - name: count-log-1
    image: busybox:1.28
    args: [/bin/sh, -c, 'tail -n+1 -F /var/log/1.log']
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  - name: count-log-2
    image: busybox:1.28
    args: [/bin/sh, -c, 'tail -n+1 -F /var/log/2.log']
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  volumes:
  - name: varlog
    emptyDir: {}
Now when you run this pod, you can access each log stream separately by running the following commands:

kubectl logs counter count-log-1
The output is similar to:

0: Fri Apr  1 11:42:26 UTC 2022
1: Fri Apr  1 11:42:27 UTC 2022
2: Fri Apr  1 11:42:28 UTC 2022
...
kubectl logs counter count-log-2
The output is similar to:

Fri Apr  1 11:42:29 UTC 2022 INFO 0
Fri Apr  1 11:42:30 UTC 2022 INFO 0
Fri Apr  1 11:42:31 UTC 2022 INFO 0
...
If you installed a node-level agent in your cluster, that agent picks up those log streams automatically without any further configuration. If you like, you can configure the agent to parse log lines depending on the source container.

Even for Pods that only have low CPU and memory usage (order of a couple of millicores for cpu and order of several megabytes for memory), writing logs to a file and then streaming them to stdout can double how much storage you need on the node. If you have an application that writes to a single file, it's recommended to set /dev/stdout as the destination rather than implement the streaming sidecar container approach.

Sidecar containers can also be used to rotate log files that cannot be rotated by the application itself. An example of this approach is a small container running logrotate periodically. However, it's more straightforward to use stdout and stderr directly, and leave rotation and retention policies to the kubelet.

Sidecar container with a logging agent
Sidecar container with a logging agent

If the node-level logging agent is not flexible enough for your situation, you can create a sidecar container with a separate logging agent that you have configured specifically to run with your application.

Note:
Using a logging agent in a sidecar container can lead to significant resource consumption. Moreover, you won't be able to access those logs using kubectl logs because they are not controlled by the kubelet.
Here are two example manifests that you can use to implement a sidecar container with a logging agent. The first manifest contains a ConfigMap to configure fluentd.

admin/logging/fluentd-sidecar-config.yaml
Copy admin/logging/fluentd-sidecar-config.yaml to clipboard
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluentd.conf: |
    <source>
      type tail
      format none
      path /var/log/1.log
      pos_file /var/log/1.log.pos
      tag count.format1
    </source>

    <source>
      type tail
      format none
      path /var/log/2.log
      pos_file /var/log/2.log.pos
      tag count.format2
    </source>

    <match **>
      type google_cloud
    </match>
Note:
In the sample configurations, you can replace fluentd with any logging agent, reading from any source inside an application container.
The second manifest describes a pod that has a sidecar container running fluentd. The pod mounts a volume where fluentd can pick up its configuration data.

admin/logging/two-files-counter-pod-agent-sidecar.yaml
Copy admin/logging/two-files-counter-pod-agent-sidecar.yaml to clipboard
apiVersion: v1
kind: Pod
metadata:
  name: counter
spec:
  containers:
  - name: count
    image: busybox:1.28
    args:
    - /bin/sh
    - -c
    - >
      i=0;
      while true;
      do
        echo "$i: $(date)" >> /var/log/1.log;
        echo "$(date) INFO $i" >> /var/log/2.log;
        i=$((i+1));
        sleep 1;
      done
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  - name: count-agent
    image: registry.k8s.io/fluentd-gcp:1.30
    env:
    - name: FLUENTD_ARGS
      value: -c /etc/fluentd-config/fluentd.conf
    volumeMounts:
    - name: varlog
      mountPath: /var/log
    - name: config-volume
      mountPath: /etc/fluentd-config
  volumes:
  - name: varlog
    emptyDir: {}
  - name: config-volume
    configMap:
      name: fluentd-config
Exposing logs directly from the application
Exposing logs directly from the application

Cluster-logging that exposes or pushes logs directly from every application is outside the scope of Kubernetes.
