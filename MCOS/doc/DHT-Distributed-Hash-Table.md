# Distributed hash table (DHT)

Source: <https://en.wikipedia.org/wiki/Distributed_hash_table>

A distributed hash table (DHT) is a class of a decentralized distributed system that provides a lookup service similar to a hash table: (key, value) pairs are stored in a DHT, and any participating node can efficiently retrieve the value associated with a given key.  Responsibility for maintaining the mapping from keys to values is distributed among the nodes, in such a way that a change in the set of participants causes a minimal amount of disruption.

DHT can scale  to extremely large numbers of nodes, and can handle continual node arrivals, departures, and failures.

## DHT properties

DHTs characteristically emphasize the following properties:

- Autonomy and decentralization: the nodes collectively form the system without any central coordination.
- Fault tolerance: the system should be reliable (in some sense) even with nodes continuously joining, leaving, and failing.
- Scalability: the system should function efficiently even with thousands or millions of nodes

A key technique used to achieve these goals is that any one node needs to coordinate with only a few other nodes in the system – most commonly, O(log n) of the n participants (see below) – so that only a limited amount of work needs to be done for each change in membership.

## Consistent hashing

Consistent hashing is a special kind of hashing such that when a hash table is resized, only K / n keys need to be remapped on average, where K is the number of keys, and n is the number of slots.

Consistent hashing employs a function **sigma(k1, k2)** that defines an abstract notion of the distance between the keys **k1** and **k2**, which is unrelated to geographical distance or network latency. Each node is assigned a single key called its identifier (ID). A node with ID **i\_x** owns all the keys **k\_m** for which **i\_x** is the closest ID, measured according to **sigma(k\_m, i\_x)**.

Example usage: Chord protocol

## Rendezvous_hashing

Rendezvous or highest random weight (HRW) hashing is an algorithm that allows clients to achieve distributed agreement on a set of k options out of a possible set of n options. A typical application is when clients need to agree on which sites (or proxies) objects are assigned to. When k is 1, it subsumes the goals of consistent hashing, using an entirely different method.

### The HRW algorithm for rendezvous hashing

Rendezvous hashing solves the distributed hash table problem: How can a set of clients, given an object O, agree on where in a set of n sites (servers, say) to place O? Each client is to select a site independently, but all clients must end up picking the same site. This is non-trivial if we add a minimal disruption constraint, and require that only objects mapping to a removed site may be reassigned to other sites.

The basic idea is to give each site Sj a score (a weight) for each object Oi, and assign the object to the highest scoring site. All clients first agree on a hash function h(). For object Oi, the site Sj is defined to have weight wi,j = h(Oi, Sj). HRW assigns Oi to the site Sm whose weight wi,m is the largest. Since h() is agreed upon, each client can independently compute the weights wi,1, wi,2, ..., wi,n and pick the largest. If the goal is distributed k-agreement, the clients can independently pick the sites with the k largest hash values.

If a site S is added or removed, only the objects mapping to S are remapped to different sites, satisfying the minimal disruption constraint above. The HRW assignment can be computed independently by any client, since it depends only on the identifiers for the set of sites S1, S2, ..., Sn and the object being assigned.

HRW easily accommodates different capacities among sites. If site Sk has twice the capacity of the other sites, we simply represent Sk twice in the list, say, as Sk,1 and Sk,2. Clearly, twice as many objects will now map to Sk as to the other sites.