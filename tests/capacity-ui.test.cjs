const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
test('capacity message is literal text and Retry still works', () => {
  class Element {
    constructor(tag) {this.tag=tag;this.children=[];this.style={};this.events={};}
    append(...children){this.children.push(...children);}
    appendChild(child){this.children.push(child);}
    addEventListener(name,callback){this.events[name]=callback;}
    set innerHTML(_value){throw Error('Do not interpolate HTML');}
  }
  const body = new Element('body');
  let retries=0;
  const context=vm.createContext({
    document:{createElement:tag=>new Element(tag),body,addEventListener(){}},
    location:{reload(){retries++;}},setTimeout(){},console,
  });
  const source=fs.readFileSync(path.join(__dirname,'../static/js/app.js'),'utf8');
  vm.runInContext(source+'; log = () => {};',context);
  vm.runInContext(`showCapacityError({message:'<img src=x onerror="bad()">',active_sessions:2,max_sessions:2})`,context);
  const content=body.children[0].children[0];
  assert.equal(content.children[1].textContent,'<img src=x onerror="bad()">');
  const button=content.children.find(e=>e.tag==='button');
  assert.equal(button.textContent,'Retry Now');
  button.events.click();assert.equal(retries,1);
});
