{ config, lib, pkgs, inputs, ... }:

{
  imports = [
    inputs.self.nixosModules.yate
    inputs.self.nixosModules.fieldpoc
  ];
  sops.secrets.ommpassword = {};
  sops.secrets.sipsecret = {};

  services.fieldpoc = {
    enable = true;
    ommIp = "omm.c3voc.de";
    ommUser = "omm";
    ommPasswordPath = config.sops.secrets.ommpassword.path;
    sipsecretPath = config.sops.secrets.sipsecret.path;
  };

  services.yate.config = {
    regexroute = "[default]
\${username}^$=-;error=noauth
\${sip_to}^\"\" <sip:\\(.*\\)@sip.plusnet.de>$=lateroute/\\1
^.*$=sip/sip:\\0;line=dialin;osip_P-Asserted-Identity=\${caller};osip_P-Preferred-Identity=\${caller};caller=1600";
    ysipchan = {
      general = {
        ignorevia = "yes";
      };
      message = {
        enable = "yes";
      };
    };
    ysnmpagent = {
      general.port = 161;
      snmp_v2.ro_community = "yate";
    };
    yrtpchan.general = {
    };
  };

  networking.firewall.allowedUDPPorts = [ 161 ];
  networking.firewall.allowedTCPPorts = [ 5060 5061 ];
  networking.nftables.extraInput = "meta l4proto udp accept";

  environment.systemPackages = with pkgs; [
    (writers.makePythonWriter python39 python39.pkgs python39.pkgs "/bin/dect_claim" { libraries = [ python39.pkgs.python-yate ]; } (builtins.readFile ./dect_claim.py))
    (runCommand "yintro.slin" {} ''
      mkdir -p $out/share/sounds/yate
      ln -s ${./yintro.slin} $out/share/sounds/yate/yintro.slin
    '')
  ];

  systemd.services.fieldpoc-nerd = {
    wantedBy = ["multi-user.target"];
    startAt = "*-*-* *:*:00";
    script = let
      reloadScript = pkgs.writeText "reload" ''
        spawn ${pkgs.inetutils}/bin/telnet localhost 9437
        expect "> "
        send "reload\n"
        expect "> "
        send "exit\n"
        expect "disconnecting"
      '';
    in ''
      ${pkgs.curl}/bin/curl https://tel.c3voc.de/export.json\?event=2 > /etc/fieldpoc/extensions.json
      ${pkgs.expect}/bin/expect ${reloadScript}
    '';
  };


  sops.secrets.trunk_password = {
    owner = "yate";
    restartUnits = [ "yate.service" ];
  };

  sops.secrets.dialout_password = {
    owner = "yate";
    restartUnits = [ "yate.service" ];
  };

  systemd.services.yate = {
    preStart = let
      accfile = pkgs.writeText "accfile.conf" (lib.generators.toINI { } {
        dialin = {
          enabled = "yes";
          protocol = "sip";
          username = "1600";
          authname = "1600";
          password = "!!trunk_password!!";
          registrar = "sip.micropoc.de";
          localaddress = "yes";
          keepalive = "25";
        };
        dialout = {
          enabled = "no";
          protocol = "sip";
          username = "53458.02";
          authname = "53458.02";
          password = "!!dialout_password!!";
          registrar = "sipm.voip2gsm.eu";
          localaddress = "yes";
          keepalive = "25";
        };
      });
    in ''
      ${pkgs.gnused}/bin/sed -e "s/!!trunk_password!!/$(cat ${config.sops.secrets.trunk_password.path})/g" -e "s/!!dialout_password!!/$(cat ${config.sops.secrets.dialout_password.path})/g" ${accfile} > /etc/yate/accfile.conf
    '';
    serviceConfig.PermissionsStartOnly = true;
  };
}
