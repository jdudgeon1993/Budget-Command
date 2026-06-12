
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_2ad9cf56427092375c681c8e9d09c930 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.recon_txs_rx_state_ ?? [],((row_rx_state_,index_86b630e3e8382622d88be192ea321cc8)=>(jsx(RadixThemesFlex,{align:"start","aria-checked":(!(reflex___state____state__cura___state____app_state.recon_unchecked_ids_rx_state_.includes(row_rx_state_?.["id"])) ? "true" : "false"),className:"rx-Stack",css:({ ["padding"] : "10px 14px", ["minHeight"] : "52px", ["borderBottom"] : "1px solid rgba(255,255,255,0.08)", ["cursor"] : "pointer", ["width"] : "100%", ["alignItems"] : "center", ["gap"] : "10px", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.08)" }), ["&:active"] : ({ ["opacity"] : "0.8" }) }),direction:"row",key:index_86b630e3e8382622d88be192ea321cc8,onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_recon_tx", ({ ["tx_id"] : row_rx_state_?.["id"] }), ({  })))], [_e], ({  })))),role:"checkbox",gap:"3"},jsx(RadixThemesBox,{css:({ ["flexShrink"] : "0" })},jsx(Fragment,{},(!(reflex___state____state__cura___state____app_state.recon_unchecked_ids_rx_state_.includes(row_rx_state_?.["id"]))?(jsx(Fragment,{},jsx("div",{className:"rx-Html",dangerouslySetInnerHTML:({ ["__html"] : "<svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"#30D158\" stroke=\"#30D158\" stroke-width=\"2\" aria-hidden=\"true\"><rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"3\"/><polyline points=\"20 6 9 17 4 12\" stroke=\"white\" stroke-width=\"2.5\" fill=\"none\"/></svg>" })},))):(jsx(Fragment,{},jsx("div",{className:"rx-Html",dangerouslySetInnerHTML:({ ["__html"] : "<svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"rgba(255,255,255,0.14)\" stroke-width=\"1.5\" aria-hidden=\"true\"><rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"3\"/></svg>" })},)))))),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex-start" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : (!(reflex___state____state__cura___state____app_state.recon_unchecked_ids_rx_state_.includes(row_rx_state_?.["id"])) ? "#FFFFFF" : "#606088"), ["fontWeight"] : "500", ["lineHeight"] : "1.2", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis", ["whiteSpace"] : "nowrap", ["maxWidth"] : "200px" })},row_rx_state_?.["desc"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["date_label"])),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontWeight"] : "700", ["color"] : (!(reflex___state____state__cura___state____app_state.recon_unchecked_ids_rx_state_.includes(row_rx_state_?.["id"])) ? row_rx_state_?.["amt_color"] : "#606088"), ["whiteSpace"] : "nowrap" })},row_rx_state_?.["amount_fmt"])))))
    )
});
