# Portal JSON-RPC specification

## portal_*RoutingTableInfo

## portal_*AddEnr

## portal_*GetEnr

## portal_*DeleteEnr

## portal_*LookupEnr

## portal_*Ping

## portal_*FindNodes

## portal_*FindContent
- must validate content

## portal_*Offer
- must not validate content
- shouldn't store data on offering node

## portal_*RecursiveFindNodes

## portal_*GetContent
- must validate content
- must check local storage first before doing recursive find content
- if recursive find content is done must do poke mechanism
- if recursive find content is done and content meets storage criteria store content
  
## portal_*TraceGetContent
- must validate content
- must check local storage first before doing recursive find content
- if recursive find content is done must do poke mechanism
- if recursive find content is done and content meets storage criteria store content

## portal_*Store
- must not validate content
  
## portal_*LocalContent
- content stored locally is assumed already validated

## portal_*Gossip
- must not validate content
- shouldn't store data on gossiping node
