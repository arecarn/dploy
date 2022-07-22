# Dploy

Dploy is a tool for creating symbolic links similarly to [GNU
Stow](https://www.gnu.org/software/stow/). It is provided as a CLI tool and
Python 3.7.2+ module and supports Windows, Linux, and OSX.

Dploy's command `stow` creates symbolic links to the contents of source
directories or packages in a specified destination directory. Repeating the
`stow` command with the same arguments will confirm that the contents of the
package have been symbolically linked.

Dploy's command `unstow` removes symbolic links that resulted from `stow`
commands. Repeating the `unstow` command with the same arguments will confirm
that the links to stowed packages have been removed.

## Installation

* Latest Release: `pip install dploy`
* Development Version: `pip install git+https://github.com/arecarn/dploy.git`

## Basic CLI Usage

* `dploy stow <source-directory>... <destination-directory>`
* `dploy unstow <source-directory>... <destination-directory>`
* `dploy --help`

## Rationale

Dploy started out as simple Python script to create symbolic links to my
dotfiles for Windows, Mac, and Linux. Over time I keep improving and tweaking my
script to suit my needs, but I was running into a problem.  Keeping all the
files I wanted to link in a config file was becoming a real pain in the neck.

I started looking for another solution to solve my problem, and found many
alternatives but none of them seemed to be a good fit. The solution that seemed
the most promising was using GNU Stow. It seemed like the most simple elegant
solution to the problem. The only issue was that it didn't support Windows.

Then I thought to myself, why can't I just create my own version of Stow that
work on Windows, Linux and OSX. So after that my I started morphing
simple python script into what would become Dploy and learned a lot more about
python in the process.

## How does it compare with GNU Stow?

Below are just a few few major points of comparison between GNU stow and Dploy.

* Like GNU Stow Dploy runs in two passes. First by collecting the actions
  required to complete the command and verifying that the command can
  completed without any issues. If no issues are detected then the second
  pass executes these actions are execute to complete the command. Otherwise
  Dploy will exit and indicate why the command can not be completed. This way a
  stow or unstow operation is atomic and never partially done.

* Like Stow, Dploy supports tree folding and tree unfolding.

* Unlike Stow, Dploy requires an explicit source(s) and a destination
  directory.

* Unlike Stow, Dploy does not have any concept of ownership, but will only
  operate on symbolic links and the creation or removal of directories for these
  symbolic links.
