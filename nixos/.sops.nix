keys:
  - &admin_hexchen age1wvtkhug4q7fcs7wz03kpn77ruqkkwp2xqq30npv4287wtf3w8ukq370vre
  - &admin_n0emis 6E10217E3187069E057DF5ABE0262A773B824745
  - &host_tel age1glkmsh6pex9g5v95vwx78a8xksmnkvsu7ccnhxzu09yvnfnjudls3lfkru

creation_rules:
  - path_regex: hosts/tel/.*
    key_groups:
    - pgp:
      - *admin_n0emis
      age:
      - *admin_hexchen
      - *host_tel