// noteの編集画面(または公開ページの編集画面)の本文を、完成稿と同じ書き方(マークダウン)で読み取る。読み取り専用。
// 使い方：ブラウザのJS実行ツールに、このファイルの中身をそのまま渡す。戻り値はJSON {title, md, counts}。
// 引用は「> 」、太字は「**」、見出しは「## 」、全角スペースだけの段落は「　」、埋め込みカードは「[カード:記事ID]」で表す。
(function(){
  const eds=[...document.querySelectorAll('[contenteditable="true"]')].sort((a,b)=>b.offsetHeight-a.offsetHeight);
  const ed=eds[0]; if(!ed) return JSON.stringify({error:'本文欄が見つかりません'});
  const inl=(n)=>{
    if(n.nodeType===3) return n.nodeValue;
    if(n.nodeType!==1) return '';
    if(n.tagName==='BR') return '\n';
    const s=[...n.childNodes].map(inl).join('');
    return (n.tagName==='STRONG'||n.tagName==='B')&&s.trim()?'**'+s+'**':s;
  };
  const out=[]; const counts={quote:0,bold:0,h2:0,card:0,space:0};
  for(const el of ed.children){
    const fig=el.tagName==='FIGURE'?el:null;
    const bq=el.tagName==='BLOCKQUOTE'?el:el.querySelector('blockquote');
    if(el.tagName==='H2'||el.tagName==='H3'){out.push('## '+el.innerText.trim());counts.h2++;continue;}
    if(bq){
      const ps=[...bq.querySelectorAll('p')];
      const lines=(ps.length?ps.map(inl):[inl(bq)]).flatMap(x=>x.replace(/\n+$/,'').split('\n')).filter(x=>x.trim());
      out.push(lines.map(l=>'> '+l).join('\n'));counts.quote++;continue;
    }
    const ifr=(fig||el).querySelector&&(fig||el).querySelector('iframe');
    if(fig||ifr){
      const m=((ifr&&ifr.src)||'').match(/notes\/(n[0-9a-z]+)/);
      out.push('[カード:'+(m?m[1]:'?')+']');counts.card++;continue;
    }
    const t=inl(el).replace(/\n+$/,'');
    if(!t.replace(/[\s　]/g,'')){ if(t.includes('　')){out.push('　');counts.space++;} continue; }
    out.push(t);
  }
  const md=out.join('\n\n');
  counts.bold=(md.match(/\*\*[^*\n]+\*\*/g)||[]).length;
  const ti=document.querySelector('textarea');
  return JSON.stringify({title:ti?ti.value:null,counts,md});
})()
