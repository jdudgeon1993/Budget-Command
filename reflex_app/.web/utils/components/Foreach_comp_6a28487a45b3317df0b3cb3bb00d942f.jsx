
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_6a28487a45b3317df0b3cb3bb00d942f = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.accounts_rows_rx_state_ ?? [],((row_rx_state_,index_a98012895d4f2dd41cdbf9714659b648)=>(jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.ledger_acct_filter_rx_state_?.valueOf?.() === row_rx_state_?.["id"]?.valueOf?.()) ? ({ ["padding"] : "5px 12px", ["border_radius"] : "20px", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["cursor"] : "pointer", ["color"] : "#BF5AF2", ["background"] : "#BF5AF218", ["border"] : "1px solid #BF5AF244", ["flex_shrink"] : "0" }) : ({ ["padding"] : "5px 12px", ["border_radius"] : "20px", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["cursor"] : "pointer", ["color"] : "#606088", ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["flex_shrink"] : "0", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),key:index_a98012895d4f2dd41cdbf9714659b648,onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_ledger_acct_filter", ({ ["value"] : ((reflex___state____state__cura___state____app_state.ledger_acct_filter_rx_state_?.valueOf?.() === row_rx_state_?.["id"]?.valueOf?.()) ? "" : row_rx_state_?.["id"]) }), ({  })))], [_e], ({  }))))},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["gap"] : "5px" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "7px", ["height"] : "7px", ["borderRadius"] : "50%", ["background"] : row_rx_state_?.["color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["whiteSpace"] : "nowrap" })},row_rx_state_?.["name"]))))))
    )
});
