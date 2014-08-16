#
BOX_URL="http://opscode-vm-bento.s3.amazonaws.com/vagrant/virtualbox/opscode_debian-7.4_chef-provisionerless.box"
BOX_RAM=256

# these should be the right incantations for headless provision on
# Debian Wheezy 7.4 (intel/64, not tried on ARM/rpi yet)
$script = <<SCRIPT
  apt-get update
  apt-get install -y python-pip python-dev
  #apt-get install -y postgresql-9.1 postgresql-client-9.1 postgresql-server-dev-9.1
  pip install setuptools
  cd /vagrant
  ./setup.py develop
SCRIPT

Vagrant.configure("2") do |config|
    config.vm.define "emfbadge" do |n|
      n.vm.hostname = "emfbadge"
      n.vm.box_url = BOX_URL
      n.vm.box = "opscode_debian-7.4_chef-provisionerless"
      n.vm.network "public_network"
      n.ssh.forward_agent = true
      n.vm.provider "virtualbox" do |v|
        v.customize ["modifyvm", :id, "--memory", BOX_RAM]
        v.customize ["modifyvm", :id, "--cpus", 1]
      end
      n.vm.provision "shell", inline: $script
    end
end
